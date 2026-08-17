import frappe
from frappe.model.document import Document


class Message(Document):
	def before_insert(self):
		self.sender = frappe.session.user
		full_name, user_image = frappe.db.get_value("User", self.sender, ["full_name", "user_image"])
		self.sender_name = full_name
		self.sender_image = user_image


def has_permission(doc, ptype=None, user=None):
	# Message only grants System Manager access at the DocType level — chat
	# access is otherwise governed entirely by chat.py's own membership
	# checks (_require_member etc.) on the whitelisted API, bypassing this
	# via ignore_permissions=True. This hook exists for a narrower purpose:
	# attachment images are uploaded private (see send_message), and a
	# private File's own has_permission falls back to *this* check once it's
	# linked to a Message (attached_to_doctype/name) — without it, only the
	# uploader could ever view an image they shared in a chat.
	user = user or frappe.session.user
	if user == "Administrator":
		return True
	return bool(frappe.db.exists("Conversation Member", {"conversation": doc.conversation, "user": user}))
