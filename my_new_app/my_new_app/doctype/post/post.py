import frappe
from frappe.model.document import Document


class Post(Document):
	def before_insert(self):
		self.author = frappe.session.user
		full_name, user_image = frappe.db.get_value("User", self.author, ["full_name", "user_image"])
		self.author_name = full_name
		self.author_image = user_image

	def before_save(self):
		if self.status == "Published" and not self.published_at:
			self.published_at = frappe.utils.now_datetime()
		if self.post_type == "Image" and self.images and not self.cover_image:
			self.cover_image = self.images[0].image

	def on_update(self):
		if self.status == "Published" and self.has_value_changed("status"):
			from my_new_app.follow import notify_followers_of_new_post

			notify_followers_of_new_post(self)

	def on_trash(self):
		_delete_comment_thread(self.name)
		frappe.db.delete("Saved Post", {"post": self.name})
		frappe.db.delete("Like", {"reference_type": "Post", "reference_name": self.name})
		frappe.db.set_value("Message", {"shared_post": self.name}, "shared_post", None)


def _delete_comment_thread(post_name):
	# Replies link back to their parent comment, so a parent can't be deleted
	# while a reply still points to it. Repeatedly delete whatever's currently
	# a leaf (nothing else references it) until the whole thread is gone,
	# which handles any depth of nesting without needing to walk the tree.
	while True:
		leaves = frappe.db.sql(
			"""
			select name from `tabPost Comment`
			where post = %s
			and name not in (
				select distinct parent_comment from `tabPost Comment`
				where post = %s and parent_comment is not null
			)
			""",
			(post_name, post_name),
		)
		if not leaves:
			break
		for (name,) in leaves:
			frappe.delete_doc("Post Comment", name, ignore_permissions=True, force=True)


def has_permission(doc, ptype=None, user=None):
	# Only read visibility is restricted here; create/write/delete are already
	# governed by the doctype's own role + if_owner permission rules. Deciding
	# read-only matters because `author` isn't set yet at create-permission
	# time (before_insert hasn't run), so applying this to "create" would
	# incorrectly deny every new post.
	if ptype != "read":
		return True
	user = user or frappe.session.user
	if doc.status == "Published":
		return True
	return doc.author == user


def get_permission_query_conditions(user=None):
	user = user or frappe.session.user
	if user == "Administrator":
		return ""
	return f"(`tabPost`.status = 'Published' OR `tabPost`.author = {frappe.db.escape(user)})"
