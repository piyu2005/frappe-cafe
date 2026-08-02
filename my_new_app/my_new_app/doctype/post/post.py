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

	def on_update(self):
		if self.status == "Published" and self.has_value_changed("status"):
			from my_new_app.follow import notify_followers_of_new_post

			notify_followers_of_new_post(self)


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
