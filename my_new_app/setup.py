import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

DEFAULT_CATEGORIES = [
	"Productivity",
	"Photography",
	"Technology",
	"Mindfulness",
	"Writing",
	"Design",
	"Culture",
]


def after_migrate():
	for title in DEFAULT_CATEGORIES:
		if not frappe.db.exists("Category", title):
			frappe.get_doc({"doctype": "Category", "title": title}).insert(ignore_permissions=True)

	# "Text" was merged into "Blog" (identical rendering, no reason for both);
	# reclassify any posts saved under the old type so the Select's remaining
	# options ("Blog"/"Image"/"Video") stay valid for every row.
	frappe.db.set_value("Post", {"post_type": "Text"}, "post_type", "Blog")

	create_custom_fields(
		{
			"User": [
				{
					"fieldname": "job_title",
					"label": "Job Title",
					"fieldtype": "Data",
					"insert_after": "bio",
				},
				{
					"fieldname": "company",
					"label": "Company",
					"fieldtype": "Data",
					"insert_after": "job_title",
				},
				{
					"fieldname": "is_private",
					"label": "Private Account",
					"fieldtype": "Check",
					"insert_after": "company",
					"default": "0",
				},
				{
					# Short one-line tagline shown under the name/username row,
					# distinct from the longer `bio` shown in the Introduction card.
					"fieldname": "headline",
					"label": "Headline",
					"fieldtype": "Data",
					"insert_after": "is_private",
				},
			]
		}
	)
