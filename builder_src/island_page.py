"""The pages that run a page of the Vue app inside a Builder page: the post
editor (/write, /write/<post>) and Messages (/messages, /messages/<id>).

Each is the Vue page as it is, built into one script and one stylesheet
(frontend/vite.island.config.js; yarn build:write, yarn build:chat; output in
public/builder_assets/<name>/) that the page loads in its <head>. The Builder
page gives it the app shell, the id in the address, and the bell of the
phone's top bar. Everything else is the Vue page's own code, so it works and
looks exactly as it does in the Vue app."""

import hashlib
from pathlib import Path

from bell import mobile_bell
from blocks import GRAY_4, INK, INK_BLACK, MUTED, OUTLINE, SURFACE_2, attribute, block, html_el, instance_of, raw_block, svg, text_style
from data_scripts import HELPERS

ASSETS = Path(__file__).resolve().parent.parent / "my_new_app" / "public" / "builder_assets"
ASSETS_URL = "/assets/my_new_app/builder_assets/"


def head_html(name):
	"""The <link> and <script> of the page, with a version so a new build is fetched."""

	def version(file):
		path = ASSETS / name / file
		return hashlib.sha1(path.read_bytes()).hexdigest()[:10] if path.exists() else "0"

	return (
		f'<link rel="stylesheet" href="{ASSETS_URL}{name}/{name}.css?v={version(name + ".css")}">\n'
		f'<script src="{ASSETS_URL}{name}/{name}.js?v={version(name + ".js")}" defer></script>'
	)


def pill(label, solid=False):
	"""A header button, drawn like frappe-ui's small Button."""
	styles = {"display": "inline-flex", "alignItems": "center", "height": "28px", "padding": "0 8px", "borderRadius": "8px", "fontSize": "14px", "letterSpacing": "0.02em"}
	styles.update({"backgroundColor": INK, "color": "#ffffff"} if solid else {"border": "1px solid #e2e2e2", "color": INK})
	return html_el("span", None, None, styles, text=label)


def header_bar(title, buttons):
	crumbs = html_el(
		"div",
		None,
		None,
		{"display": "flex", "gap": "4px", "fontSize": "16px", "fontWeight": "500", "letterSpacing": "0.015em", "color": MUTED},
		[html_el("span", text="Cafe"), html_el("span", None, None, {"color": GRAY_4}, text="/"), html_el("span", None, None, {"color": INK_BLACK}, text=title)],
	)
	return html_el(
		"div",
		None,
		None,
		{"display": "flex", "alignItems": "center", "justifyContent": "space-between", "height": "48px", "flexShrink": "0", "padding": "0 20px", "borderBottom": f"1px solid {OUTLINE}"},
		[crumbs, html_el("div", None, None, {"display": "flex", "gap": "8px"}, buttons)],
	)


def write_skeleton():
	icons = "".join(svg(name, 16, MUTED) for name in ("bold", "italic", "underline", "strikethrough", "heading", "quote", "list", "list-ordered", "align-left", "image", "link"))
	toolbar = html_el("div", None, None, {"display": "flex", "gap": "14px", "alignItems": "center", "width": "fit-content", "padding": "11px 16px", "border": "1px solid #e2e2e2", "borderRadius": "9999px"}, [icons])
	title = html_el("div", None, None, {"marginTop": "16px", **text_style(30, "600", GRAY_4, "0", "1.25")}, text="Give your story a title")
	story = html_el("div", None, None, {"marginTop": "16px", **text_style(16, "420", GRAY_4, "0.02em", "1.6")}, text="Tell your story\u2026")
	body = html_el("div", None, None, {"width": "100%", "maxWidth": "600px", "margin": "0 auto", "padding": "40px 0"}, [toolbar, title, story])
	return header_bar("Write", [pill("Save Draft"), pill("Publish", True)]) + body


def chat_skeleton():
	bars = "".join(
		html_el("div", None, None, {"display": "flex", "gap": "12px", "alignItems": "center", "padding": "10px 12px"}, [
			html_el("span", None, None, {"width": "24px", "height": "24px", "borderRadius": "9999px", "backgroundColor": SURFACE_2}),
			html_el("div", None, None, {"flex": "1"}, [
				html_el("div", None, None, {"width": "50%", "height": "10px", "borderRadius": "5px", "backgroundColor": SURFACE_2}),
				html_el("div", None, None, {"width": "75%", "height": "8px", "marginTop": "8px", "borderRadius": "4px", "backgroundColor": SURFACE_2}),
			]),
		])
		for _ in range(4)
	)
	search = html_el("div", None, None, {"padding": "12px", "borderBottom": f"1px solid {OUTLINE}"}, [html_el("div", None, None, {"height": "28px", "borderRadius": "8px", "backgroundColor": SURFACE_2})])
	left = html_el("div", None, None, {"width": "320px", "flexShrink": "0", "borderRight": f"1px solid {OUTLINE}"}, [search, bars])
	right = html_el("div", None, None, {"flex": "1", "display": "grid", "placeItems": "center", **text_style(14, "420", "#525252")}, text="Select a conversation to start messaging.")
	return header_bar("Messages", [pill("New group")]) + html_el("div", None, None, {"display": "flex", "flex": "1", "minHeight": "0"}, [left, right])


SKELETONS = {"write": write_skeleton, "chat": chat_skeleton}


def build_island(name, id_attr, shell_id, shell_block):
	"""The shell and a box the Vue page mounts in. `id_attr` is the data
	attribute that carries the id from the address (data.w.id)."""
	root = block(
		"div",
		"Page",
		attrs={"id": f"mna-{name}-root"},
		custom={id_attr: ""},
		styles={"display": "flex", "flexDirection": "column", "width": "100%", "height": "100%", "minHeight": "0"},
		# What Builder's editor and the folder thumbnail show, since neither runs the
		# page's script. The Vue page replaces it when it starts.
		children=[raw_block("Preview", SKELETONS[name](), ["mna-skeleton-page"], styles={"display": "flex", "flexDirection": "column", "flex": "1", "minHeight": "0"})],
	)
	root = attribute(root, "w.id", id_attr)
	bell = raw_block("Bell template", html_el("template", None, {"id": "mna-bell-template"}, None, [mobile_bell()]), styles={"display": "none"})
	main = block(
		"div",
		"Main",
		["mna-main", "mna-island-main"],
		styles={"display": "flex", "flexGrow": "1", "flexDirection": "column", "minWidth": "0", "height": "100vh", "overflow": "hidden"},
		children=[root, bell],
	)
	app = block(
		"div",
		"App",
		["mna-app"],
		styles={"display": "flex", "width": "100%", "height": "100vh", "backgroundColor": "#ffffff", **text_style(14, "420", INK_BLACK, "0.02em", "1.15")},
		children=[instance_of(shell_id, shell_block, "Shell"), main],
	)
	top = block("div", None, children=[app])
	top["blockId"] = "root"
	top["originalElement"] = "body"
	return [top]


def build_write(shell_id, shell_block):
	return build_island("write", "data-post", shell_id, shell_block)


def build_chat(shell_id, shell_block):
	return build_island("chat", "data-conversation", shell_id, shell_block)


def data_script(page, param):
	"""Sends a guest to sign in first; the Vue page loads everything else."""
	return HELPERS + f'''\
item = frappe.form_dict.{param} or ""

if frappe.session.user == "Guest":
    redirect("/login?redirect=/{page}" + ("/" + path_segment(item) if item else ""))

data.w = {{"id": clean(item)}}
'''


WRITE_DATA_SCRIPT = data_script("write", "post_id")
CHAT_DATA_SCRIPT = data_script("messages", "conversation_id")
