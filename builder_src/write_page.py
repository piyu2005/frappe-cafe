"""The post editor: /write and /write/<post>.

The editor is the Vue app's own WritePost.vue, built into one script and one
stylesheet (frontend/vite.write.config.js, output in public/builder_assets/
write/) that this page loads in its <head>. This page gives it the app shell,
the post's id, and the bell of the phone's top bar. Everything else, the toolbar,
the story preview and saving, is the editor's own code, so it works and
looks exactly as it does in the Vue app."""

import hashlib
from pathlib import Path

from bell import mobile_bell
from data_scripts import HELPERS
from blocks import INK_BLACK, attribute, block, html_el, instance_of, raw_block, text_style

WRITE_BUILD = Path(__file__).resolve().parent.parent / "my_new_app" / "public" / "builder_assets" / "write"
WRITE_ROOT = "/assets/my_new_app/builder_assets/write/"


def head_html():
	"""The <link> and <script> of the editor, with a version so a new build is fetched."""
	def version(name):
		path = WRITE_BUILD / name
		return hashlib.sha1(path.read_bytes()).hexdigest()[:10] if path.exists() else "0"

	return (
		f'<link rel="stylesheet" href="{WRITE_ROOT}write.css?v={version("write.css")}">\n'
		f'<script src="{WRITE_ROOT}write.js?v={version("write.js")}" defer></script>'
	)


def build_write(shell_id, shell_block):
	root = block("div", "Editor", attrs={"id": "mna-write-root"}, custom={"data-post": ""}, styles={"display": "flex", "flexDirection": "column", "width": "100%", "height": "100%", "minHeight": "0"})
	root = attribute(root, "w.post_id", "data-post")
	bell = raw_block("Bell template", html_el("template", None, {"id": "mna-bell-template"}, None, [mobile_bell()]), styles={"display": "none"})
	main = block(
		"div",
		"Main",
		["mna-main", "mna-write-main"],
		styles={"display": "flex", "flexGrow": "1", "flexDirection": "column", "minWidth": "0", "height": "100vh", "overflow": "hidden"},
		children=[root, bell],
	)
	app = block(
		"div",
		"App",
		["mna-app"],
		styles={
			"display": "flex",
			"width": "100%",
			"height": "100vh",
			"backgroundColor": "#ffffff",
			**text_style(14, "420", INK_BLACK, "0.02em", "1.15"),
		},
		children=[instance_of(shell_id, shell_block, "Shell"), main],
	)
	top = block("div", None, children=[app])
	top["blockId"] = "root"
	top["originalElement"] = "body"
	return [top]


# The editor loads the post itself. This only sends a guest to sign in first.
WRITE_MAIN = """\
post_id = frappe.form_dict.post_id or ""

if frappe.session.user == "Guest":
    redirect("/login?redirect=/write" + ("/" + path_segment(post_id) if post_id else ""))

data.w = {"post_id": clean(post_id)}
"""

WRITE_DATA_SCRIPT = HELPERS + WRITE_MAIN
