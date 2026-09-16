import frappe

# Frappe core hardcodes a website_route_rules entry (frappe/hooks.py:
# {"from_route": "/profile", "to_route": "me"}) that rewrites any request to
# "/profile" into the endpoint "me" BEFORE our own catch-all wildcard rule
# (a dynamic "/<path:app_path>" rule) is even considered - Werkzeug always
# tries a static rule like "/profile" before a dynamic one, regardless of
# hook/app order. That endpoint then renders frappe/www/me.py, which
# explicitly frappe.throw()s a PermissionError for Guest - hence the SPA's
# public /profile/:userId? view getting a 403 "Not Permitted" instead of
# ever loading. The fix isn't to reclaim "/profile" (we can't out-rank a
# static Werkzeug rule with our dynamic one) - it's to override what "me"
# itself renders. Page-override precedent: frappe/website/page_renderers/
# template_page.py walks installed_apps in reverse, so this app's own
# www/me.html wins over frappe's - same mechanism as login.html and
# update-password.html. me.html itself is just a build-time copy of
# index.html (see frontend/package.json's "postbuild" script), so this
# controller mirrors index.py's own context exactly. The browser's address
# bar keeps showing "/profile" (this is an internal endpoint rewrite, not an
# HTTP redirect), so the SPA's own router.js still matches its
# /profile/:userId? route correctly once it hydrates.
no_cache = 1


def get_context(context):
	csrf_token = frappe.sessions.get_csrf_token()
	frappe.db.commit()
	context.csrf_token = csrf_token
	context.site_name = frappe.local.site
