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
from blocks import INK_BLACK, attribute, block, html_el, instance_of, raw_block, text_style
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


def build_island(name, id_attr, shell_id, shell_block):
	"""The shell and a box the Vue page mounts in. `id_attr` is the data
	attribute that carries the id from the address (data.w.id)."""
	root = block(
		"div",
		"Page",
		attrs={"id": f"mna-{name}-root"},
		custom={id_attr: ""},
		styles={"display": "flex", "flexDirection": "column", "width": "100%", "height": "100%", "minHeight": "0"},
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
