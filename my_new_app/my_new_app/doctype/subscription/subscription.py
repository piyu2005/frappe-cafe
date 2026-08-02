import frappe
from frappe.model.document import Document


class Subscription(Document):
	def before_insert(self):
		# Usually the session user subscribing to something themselves, but
		# accepting a Follow Request creates this on behalf of the requester.
		if not self.subscriber:
			self.subscriber = frappe.session.user
