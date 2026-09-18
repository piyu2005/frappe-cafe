import frappe


def execute():
	"""Private accounts and the follow feature are gone - every account is
	public now, and message requests are decided purely by "is this our first
	conversation" rather than a follow relationship. Cleans up what they left
	behind: the old follow-only Subscription rows (Publication subscriptions,
	a separate use of the same doctype, are untouched), the now-orphaned
	Follow Request doctype and its table, the User.is_private custom field,
	and any App Notification rows of the types that only follow ever created."""
	frappe.db.delete("Subscription", {"reference_doctype": "User"})

	frappe.db.delete(
		"App Notification", {"type": ["in", ["Follow Request", "Follow Accepted", "New Follower", "New Post"]]}
	)

	if frappe.db.exists("DocType", "Follow Request"):
		frappe.delete_doc("DocType", "Follow Request", ignore_permissions=True, force=True)

	frappe.db.delete("Custom Field", {"dt": "User", "fieldname": "is_private"})
	# Deleting the Custom Field record only drops the column on the *next*
	# schema sync - dropping it here directly means one migrate is enough.
	if frappe.db.has_column("User", "is_private"):
		frappe.db.sql("ALTER TABLE `tabUser` DROP COLUMN `is_private`")
	frappe.clear_cache(doctype="User")
