import frappe
from frappe.model.document import Document


class FollowRequest(Document):
	def before_insert(self):
		self.from_user = frappe.session.user
