import frappe

# See www/me.py - it's a byte-for-byte copy of this page (kept in sync by
# frontend/package.json's "postbuild" script), needed only to override what
# frappe core's own www/me.py renders (frappe/hooks.py rewrites "/profile"
# to the "me" endpoint - see www/me.py for the full explanation).
no_cache = 1


def get_context(context):
	csrf_token = frappe.sessions.get_csrf_token()
	frappe.db.commit()
	context.csrf_token = csrf_token
	context.site_name = frappe.local.site
