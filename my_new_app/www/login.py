# NOTE: this file is currently dead code, kept only because deleting it
# requires a destructive step outside this session's permissions — it should
# be removed the next time this app's www/ overrides are touched.
#
# It originally existed (PR #15) to redirect a Guest hitting bare "/login"
# into the old "/frontend/login" prefix. Now that the SPA is served at the
# site root, hooks.py's own catch-all website_route_rules entry
# ("/<path:app_path>" -> "index") matches "/login" itself before Frappe's
# page-name resolution ever gets to this file (Werkzeug tries route rules
# before falling back to a literal www/<name> lookup), so this get_context()
# never runs any more - both branches below are fully superseded:
# frontend/src/router.js's beforeEach guard already redirects an
# unauthenticated visitor to its own Login view (the Guest branch here), and
# already bounces an already-authenticated visitor away from "/login" (the
# logged-in branch here, which used to delegate to frappe's own
# frappe/www/login.py for that).
import frappe


def get_context(context):
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/"
		raise frappe.Redirect

	from frappe.www.login import get_context as default_login_context

	return default_login_context(context)
