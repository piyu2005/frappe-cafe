import frappe


def get_context(context):
	# Frappe core hardcodes "/" as the fallback destination for its OAuth
	# failure pages (frappe.respond_as_web_page's default primary_action) and
	# a Guest visiting "/" resolves to this "login" page (see
	# frappe/website/utils.py's get_home_page) — so this file, not any hook,
	# is what actually catches "Home" after a broken/expired Google sign-in
	# and sends people to our own styled login page instead of core Frappe's.
	# Page-override precedent: frappe/website/page_renderers/template_page.py
	# walks installed_apps in reverse, so this app's www/login.html wins over
	# frappe's own (see update-password.html for the same mechanism).
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/frontend/login"
		raise frappe.Redirect

	# A logged-in user landing here (e.g. a stale bookmark) should keep
	# getting Frappe's normal bounce-to-desk/home behavior, not our SPA's
	# login page — delegate to core's own context builder for that case.
	from frappe.www.login import get_context as default_login_context

	return default_login_context(context)
