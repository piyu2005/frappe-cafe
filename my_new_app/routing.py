"""Serves the Builder Home page at the site root, and only while it is published.

Every path that has no page of its own goes to the Vue app (see the catch-all in
hooks.py), and "/" is one of them. Builder's own way to take "/" is its home
page setting, but that has two problems here. The catch-all swallows the page
it points to, and if that page were unpublished, "/" would show a 404 instead
of going back to the Vue app.

This renderer avoids both. It is tried before Builder's own (this app comes
first in the app order), it only answers for "/", and it only answers while the
"mna-home" page is published. Unpublish that page in Builder and "/" is the Vue
app again, with nothing else to undo.
"""

import frappe

HOME_ROUTE = "mna-home"

try:
	from builder.builder.doctype.builder_page.builder_page import BuilderPageRenderer
except ImportError:  # Builder is not installed: "/" stays with the Vue app
	BuilderPageRenderer = None


def is_root_request():
	request = getattr(frappe.local, "request", None)
	return bool(request) and request.path in ("", "/")


if BuilderPageRenderer:

	class HomeRenderer(BuilderPageRenderer):
		def can_render(self):
			if not is_root_request():
				return False
			self.path = HOME_ROUTE
			return super().can_render()

else:

	class HomeRenderer:
		def __init__(self, path, http_status_code=None):
			pass

		def can_render(self):
			return False
