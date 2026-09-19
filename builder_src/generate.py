"""Generates the Builder files in my_new_app/builder_files/ from the sources here.

Builder stores pages, components and scripts as JSON that is long and hard to
review. The sources of truth are the plain files in this folder (styles.css,
shell.js, search.js) and this script. Run it after changing any of them:

	python3 apps/my_new_app/builder_src/generate.py

Styling is split on purpose. Everything static (sizes, colors, spacing, layout)
is set on the blocks, because Builder's editor canvas shows only block styles:
it never loads a page's CSS script. styles.css keeps what a block cannot
express: hover and focus states, the mobile layout (Builder's own breakpoints
are 576 and 1024px, ours is 768px), fonts, and the elements JavaScript creates.

Then run `bench migrate` (or reload the site) to import the result. Builder
only imports a file whose `modified` is newer than the copy in the database, so
every run stamps the current time.
"""

import hashlib
import html as htmllib
import json
import random
import re
import shutil
from datetime import datetime
from pathlib import Path

SRC = Path(__file__).resolve().parent
REPO = SRC.parent
APP = REPO / "my_new_app"
OUT = APP / "builder_files"
FONTS_OUT = APP / "public" / "builder_assets" / "fonts"
LUCIDE = REPO / "frontend" / "node_modules" / "lucide-static" / "icons"
FONT_FILES = {REPO / "frontend" / "src" / "assets" / "Newsreader" / "Newsreader-Regular.woff2"}

NOW = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
_ids = random.Random("my_new_app.builder")


def block_id():
	return "".join(_ids.choices("0123456789abcdefghijklmnopqrstuvwxyz", k=9))


def slug(name):
	return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


# ---- Blocks ----

INK = "#171717"
INK_BLACK = "#0f0f0f"
MUTED = "#7c7c7c"
OUTLINE = "#ededed"
SURFACE_1 = "#f8f8f8"
SURFACE_2 = "#f3f3f3"
DIALOG_SHADOW = "0 0 0 1px rgba(0, 0, 0, 0.08), 0 8px 24px rgba(0, 0, 0, 0.12)"


def block(element, name=None, classes=(), attrs=None, custom=None, text=None, children=(), html=None, styles=None):
	"""`styles` are the block's static CSS (camelCase keys, as Builder stores them).
	`text` is plain text, shown by Builder as the block's innerHTML. `html` is
	raw markup (used for svg icons) and is marked as a raw-html block."""
	if text is not None:
		html_content, raw = htmllib.escape(text), False
	else:
		html_content, raw = html, bool(html)
	return {
		"attributes": attrs or {},
		"baseStyles": styles or {},
		"blockId": block_id(),
		"blockName": name,
		"children": list(children),
		"classes": list(classes),
		"clientScript": {},
		"customAttributes": custom or {},
		"dataKey": None,
		"draggable": False,
		"dynamicValues": [],
		"element": element,
		"elementBeforeConversion": None,
		"extendedFromComponent": None,
		"innerHTML": html_content,
		"isChildOfComponent": None,
		"isRepeaterBlock": False,
		"mobileStyles": {},
		"originalElement": "__raw_html__" if raw else None,
		"props": {},
		"rawStyles": {},
		"referenceBlockId": None,
		"tabletStyles": {},
		"visibilityCondition": None,
	}


def icon(name, size, color=None, styles=None):
	"""A lucide icon as an inline svg. Builder wraps it in a div, and that div
	carries the size, so the svg just fills it. The stroke is 1.5, not lucide's
	2, because that is what frappe-ui draws."""
	source = (LUCIDE / f"{name}.svg").read_text()
	inner = re.search(r"<svg[^>]*>(.*)</svg>", source, re.S).group(1).strip()
	markup = (
		'<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 24 24" fill="none" '
		'stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" '
		f'aria-hidden="true" style="display:block">{inner}</svg>'
	)
	box = {"width": f"{size}px", "height": f"{size}px", "flexShrink": "0"}
	if color:
		box["color"] = color
	return block("svg", f"icon/{name}", html=markup, styles={**box, **(styles or {})})


def instance_of(component_id, component_block, name):
	"""A page's reference to a component. Builder rebuilds the children of a
	component from the instance's children, matched by `referenceBlockId`, so
	the instance needs one empty child per child of the component."""

	def mirror(source):
		node = block(None, children=[mirror(child) for child in source.get("children") or []])
		node["isChildOfComponent"] = component_id
		node["referenceBlockId"] = source["blockId"]
		return node

	node = block(None, name=name, children=[mirror(c) for c in component_block.get("children") or []])
	node["extendedFromComponent"] = component_id
	return node


# ---- Shell component ----

NAV_ITEMS = [
	("home", "Home", "/", "house"),
	("search", "Search", "/search", "search"),
	("messages", "Messages", "/messages", "message-circle"),
	("profile", "Profile", "/profile", "user"),
]
TAB_ITEMS = NAV_ITEMS + [("settings", "Settings", "/settings", "settings")]

BADGE_STYLES = {
	"display": "none",
	"position": "absolute",
	"top": "-4px",
	"right": "-6px",
	"minWidth": "16px",
	"height": "16px",
	"padding": "0 4px",
	"borderRadius": "8px",
	"backgroundColor": "#e03636",
	"color": "#ffffff",
	"fontSize": "10px",
	"fontWeight": "500",
	"lineHeight": "16px",
	"letterSpacing": "0",
	"textAlign": "center",
}
RAIL_ITEM_STYLES = {
	"position": "relative",
	"display": "grid",
	"placeItems": "center",
	"flexShrink": "0",
	"width": "28px",
	"height": "28px",
	"borderRadius": "8px",
	"color": INK,
}
MENU_ITEM_STYLES = {
	"display": "flex",
	"alignItems": "center",
	"gap": "8px",
	"width": "100%",
	"height": "28px",
	"padding": "0 8px",
	"border": "0",
	"borderRadius": "6px",
	"backgroundColor": "transparent",
	"color": INK,
	"fontSize": "14px",
	"textAlign": "left",
	"cursor": "pointer",
}


def badge():
	return block("span", "Unread badge", ["mna-badge"], custom={"data-badge": "messages"}, styles=BADGE_STYLES)


def rail_item(key, label, href, icon_name):
	children = [icon(icon_name, 16)]
	if key == "messages":
		children.append(badge())
	return block(
		"a",
		label,
		["mna-rail-item"],
		attrs={"href": href, "title": label, "aria-label": label},
		custom={"data-nav": key},
		children=children,
		styles=RAIL_ITEM_STYLES,
	)


def tab_item(key, label, href, icon_name):
	"""Mobile bottom-bar tab. Its look is in styles.css, under the 768px media
	query, because Builder has no breakpoint at that width."""
	children = [icon(icon_name, 24, styles={"color": "inherit"})]
	if key == "messages":
		children.append(badge())
	return block(
		"a",
		label,
		["mna-tab"],
		attrs={"href": href, "aria-label": label},
		custom={"data-nav": key},
		children=children,
	)


def build_shell():
	logo = block(
		"button",
		"Logo",
		["mna-logo"],
		attrs={"id": "mna-logo", "type": "button", "aria-label": "Cafe menu", "aria-haspopup": "menu"},
		children=[icon("feather", 16)],
		styles={
			"display": "grid",
			"placeItems": "center",
			"flexShrink": "0",
			"width": "32px",
			"height": "32px",
			"margin": "0 -2px",
			"padding": "0",
			"border": "0",
			"borderRadius": "8px",
			"backgroundColor": INK,
			"color": "#ffffff",
			"cursor": "pointer",
		},
	)
	rail = block(
		"nav",
		"Rail",
		["mna-rail"],
		attrs={"aria-label": "Main"},
		children=[logo] + [rail_item(*item) for item in NAV_ITEMS],
		styles={
			"display": "flex",
			"flexDirection": "column",
			"alignItems": "center",
			"gap": "12px",
			"flexShrink": "0",
			"width": "50px",
			"padding": "10px 11px 12px",
			"backgroundColor": SURFACE_1,
			"borderRight": f"1px solid {OUTLINE}",
		},
	)
	bottom_nav = block(
		"nav",
		"Bottom bar",
		["mna-bottom-nav"],
		attrs={"aria-label": "Main"},
		children=[tab_item(*item) for item in TAB_ITEMS],
		styles={"display": "none"},
	)
	menu = block(
		"div",
		"Logo menu",
		["mna-menu"],
		attrs={"id": "mna-menu", "role": "menu"},
		children=[
			block(
				"a",
				"Settings",
				["mna-menu-item"],
				attrs={"href": "/settings", "role": "menuitem"},
				children=[icon("settings", 16, MUTED), block("span", text="Settings")],
				styles=MENU_ITEM_STYLES,
			),
			block(
				"button",
				"Logout",
				["mna-menu-item"],
				attrs={"id": "mna-logout", "type": "button", "role": "menuitem"},
				children=[icon("log-out", 16, MUTED), block("span", text="Logout")],
				styles=MENU_ITEM_STYLES,
			),
		],
		styles={
			"display": "none",
			"position": "fixed",
			"top": "46px",
			"left": "8px",
			"zIndex": "50",
			"minWidth": "176px",
			"padding": "4px",
			"borderRadius": "8px",
			"backgroundColor": "#ffffff",
			"boxShadow": DIALOG_SHADOW,
		},
	)
	# display: contents keeps this wrapper out of the page layout: the rail and
	# main column stay direct flex children of the app container.
	return block("div", "Shell", ["mna-shell"], children=[rail, bottom_nav, menu], styles={"display": "contents"})


# ---- Search page ----

def bind(key, prop, kind):
	"""A binding of a block property to a key of the data script's data. Inside a
	repeater the key is looked up on the current item."""
	return {"comesFrom": "dataScript", "key": key, "property": prop, "type": kind}


def build_person_row():
	"""The template row of the list. Builder repeats it once per person in
	`data.people`, on the server, so the first paint already has the names. The
	look duplicates .mna-person in styles.css, which styles the rows that
	search.js creates while typing."""
	avatar_image = block(
		"img",
		"Avatar image",
		attrs={"src": "", "alt": ""},
		styles={"gridArea": "1 / 1", "width": "100%", "height": "100%", "objectFit": "cover"},
	)
	avatar_image["dynamicValues"] = [bind("user_image", "src", "attribute")]
	avatar_image["visibilityCondition"] = {"key": "user_image", "comesFrom": "dataScript"}
	# Both avatar children share one grid cell. On the page only one of them is
	# rendered; the editor canvas ignores the conditions and shows both.
	avatar_initial = block("span", "Avatar initial", classes=["initial"], text="P", styles={"gridArea": "1 / 1"})
	avatar_initial["dynamicValues"] = [bind("initial", "innerHTML", "key")]
	avatar_initial["visibilityCondition"] = {"key": "no_image", "comesFrom": "dataScript"}
	avatar = block(
		"span",
		"Avatar",
		["mna-avatar"],
		children=[avatar_image, avatar_initial],
		styles={
			"display": "grid",
			"placeItems": "center",
			"flexShrink": "0",
			"width": "32px",
			"height": "32px",
			"overflow": "hidden",
			"borderRadius": "9999px",
			"backgroundColor": SURFACE_2,
			"color": MUTED,
			"fontSize": "16px",
			"fontWeight": "500",
			"letterSpacing": "0.02em",
			"textTransform": "uppercase",
		},
	)
	name = block(
		"span",
		"Name",
		["mna-person-name"],
		text="Priyanshi Hodage",
		styles={
			"overflow": "hidden",
			"fontSize": "16px",
			"letterSpacing": "0.02em",
			"color": "#000000",
			"textOverflow": "ellipsis",
			"whiteSpace": "nowrap",
		},
	)
	name["dynamicValues"] = [bind("full_name", "innerHTML", "key")]
	row = block(
		"a",
		"Person",
		["mna-person"],
		attrs={"href": "/profile"},
		children=[avatar, name],
		styles={
			"display": "flex",
			"alignItems": "center",
			"gap": "12px",
			"height": "44px",
			"padding": "6px 8px",
			"borderRadius": "8px",
		},
	)
	row["dynamicValues"] = [bind("href", "href", "attribute")]
	return row


def build_search(shell_id, shell_block):
	header = block(
		"header",
		"Header",
		["mna-header"],
		styles={
			"display": "flex",
			"flexShrink": "0",
			"alignItems": "center",
			"justifyContent": "space-between",
			"height": "48px",
			"padding": "0 20px",
			"borderBottom": f"1px solid {OUTLINE}",
			"backgroundColor": "#ffffff",
		},
		children=[
			block(
				"div",
				"Breadcrumbs",
				["mna-crumbs"],
				styles={
					"display": "flex",
					"alignItems": "center",
					"gap": "4px",
					"paddingLeft": "2px",
					"fontSize": "16px",
					"fontWeight": "500",
					"letterSpacing": "0.015em",
					"color": MUTED,
				},
				children=[
					block("a", text="Cafe", attrs={"href": "/"}),
					block(
						"span",
						classes=["sep"],
						text="/",
						styles={"color": "#999999", "fontSize": "14px", "fontWeight": "420", "letterSpacing": "0.02em"},
					),
					block("span", classes=["current"], text="Explore", styles={"color": INK_BLACK}),
				],
			),
			block(
				"a",
				"New Post",
				["mna-btn", "mna-btn-solid"],
				attrs={"href": "/write"},
				styles={
					"display": "inline-flex",
					"alignItems": "center",
					"justifyContent": "center",
					"gap": "8px",
					"height": "28px",
					"padding": "0 8px",
					"borderRadius": "8px",
					"backgroundColor": INK,
					"color": "#ffffff",
					"fontSize": "14px",
					"whiteSpace": "nowrap",
				},
				children=[icon("plus", 16), block("span", text="New Post")],
			),
		],
	)
	search_box = block(
		"div",
		"Search box",
		["mna-search"],
		styles={"position": "relative", "display": "block", "marginTop": "8px"},
		children=[
			icon("search", 16, MUTED, styles={"position": "absolute", "top": "6px", "left": "8px", "pointerEvents": "none"}),
			block(
				"input",
				"Search input",
				attrs={
					"id": "mna-search-input",
					"type": "text",
					"placeholder": "Search",
					"aria-label": "Search writers",
					"autocomplete": "off",
				},
				styles={
					"display": "block",
					"width": "100%",
					"height": "28px",
					"padding": "6px 8px 6px 32px",
					"border": f"1px solid {SURFACE_2}",
					"borderRadius": "8px",
					"outline": "none",
					"backgroundColor": SURFACE_2,
					"color": INK,
					"fontSize": "14px",
					"letterSpacing": "0.02em",
				},
			),
		],
	)
	people = block(
		"div",
		"People",
		["mna-people"],
		attrs={"id": "mna-people", "aria-live": "polite"},
		styles={"display": "flex", "flexDirection": "column", "gap": "4px", "marginTop": "16px"},
		children=[build_person_row()],
	)
	people["isRepeaterBlock"] = True
	people["dataKey"] = bind("people", "innerHTML", "key")
	container = block(
		"section",
		"Container",
		["mna-container"],
		styles={"width": "100%", "maxWidth": "640px", "margin": "0 auto", "padding": "32px 20px"},
		children=[
			block(
				"h1",
				"Title",
				["mna-title"],
				text="Writers at Cafe",
				styles={
					"margin": "0",
					"fontFamily": "Newsreader",
					"fontSize": "32px",
					"fontWeight": "400",
					"lineHeight": "1.6",
					"letterSpacing": "0.015em",
					"color": "#000000",
				},
			),
			search_box,
			people,
		],
	)
	main = block(
		"div",
		"Main",
		["mna-main"],
		styles={"display": "flex", "flexGrow": "1", "flexDirection": "column", "minWidth": "0"},
		children=[
			header,
			block(
				"div",
				"Scroll area",
				["mna-scroll"],
				styles={"flexGrow": "1", "minHeight": "0", "overflowY": "auto"},
				children=[container],
			),
		],
	)
	app = block(
		"div",
		"App",
		["mna-app"],
		styles={
			"display": "flex",
			# 100%, not 100vw: in the editor canvas vw is the whole browser window,
			# which is wider than the canvas and clips the right edge.
			"width": "100%",
			"height": "100vh",
			"overflow": "hidden",
			"backgroundColor": "#ffffff",
			"color": INK_BLACK,
			"fontSize": "14px",
			"fontWeight": "420",
			"lineHeight": "1.15",
			"letterSpacing": "0.02em",
		},
		children=[instance_of(shell_id, shell_block, "Shell"), main],
	)
	root = block("div", None, children=[app])
	root["blockId"] = "root"
	root["originalElement"] = "body"
	return [root]


# ---- Documents ----


def client_script(name, script_type, source, idx):
	return {
		"creation": NOW,
		"docstatus": 0,
		"doctype": "Builder Client Script",
		"idx": idx,
		"modified": NOW,
		"modified_by": "Administrator",
		"name": name,
		"owner": "Administrator",
		"script": source,
		"script_type": script_type,
	}


def component(component_id, name, root_block):
	return {
		"block": json.dumps(root_block),
		"component_data_script": None,
		"component_id": component_id,
		"component_name": name,
		"creation": NOW,
		"docstatus": 0,
		"doctype": "Builder Component",
		"for_web_page": None,
		"idx": 0,
		"modified": NOW,
		"modified_by": "Administrator",
		"name": component_id,
		"owner": "Administrator",
	}


def page(name, title, route, blocks, script_names, data_script):
	return {
		"app": "my_new_app",
		"authenticated_access": 0,
		"blocks": blocks,
		"client_scripts": [{"builder_script": script} for script in script_names],
		"creation": NOW,
		"disable_indexing": 1,
		"docstatus": 0,
		"doctype": "Builder Page",
		"draft_blocks": None,
		"dynamic_route": 0,
		"head_html": None,
		"idx": 0,
		"is_standard": 1,
		"is_template": 0,
		"modified": NOW,
		"modified_by": "Administrator",
		"name": name,
		"owner": "Administrator",
		"page_data_script": data_script,
		"page_name": name,
		"page_title": title,
		"project_folder": "my_new_app",
		"published": 1,
		"published_at": NOW,
		"route": route,
	}


def write_json(kind, name, doc):
	folder = OUT / kind / slug(name)
	folder.mkdir(parents=True, exist_ok=True)
	(folder / f"{slug(name)}.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")


# Runs on the server for every visit. Builder puts what it returns into the
# page as raw HTML (its template engine does not escape), and a name is chosen
# by the user, so every value that reaches the HTML is escaped here.
SEARCH_DATA_SCRIPT = """\
if frappe.session.user == "Guest":
    redirect("/login?redirect=/search")

people = frappe.call("my_new_app.api.list_people")
for person in people:
    identifier = person.get("username") or person.get("name")
    label = person.get("full_name") or identifier
    segment = identifier
    for char, code in (("%", "%25"), ("/", "%2F"), ("?", "%3F"), ("#", "%23"), ("\\\\", "%5C"), (" ", "%20")):
        segment = segment.replace(char, code)
    person["href"] = frappe.utils.escape_html("/profile/" + segment)
    person["full_name"] = frappe.utils.escape_html(label)
    person["initial"] = frappe.utils.escape_html(label.strip()[:1])
    image = person.get("user_image") or ""
    person["user_image"] = frappe.utils.escape_html(image) if image.startswith(("/", "https://", "http://")) else ""
    person["no_image"] = not person["user_image"]
data.people = people
"""


def main():
	if OUT.exists():
		shutil.rmtree(OUT)

	FONTS_OUT.mkdir(parents=True, exist_ok=True)
	for font in FONT_FILES:
		shutil.copy(font, FONTS_OUT / font.name)

	write_json("client_scripts", "MNA Styles", client_script("MNA Styles", "CSS", (SRC / "styles.css").read_text(), 1))
	write_json("client_scripts", "MNA Shell", client_script("MNA Shell", "JavaScript", (SRC / "shell.js").read_text(), 2))
	write_json("client_scripts", "MNA Search", client_script("MNA Search", "JavaScript", (SRC / "search.js").read_text(), 3))

	shell_id = hashlib.sha1(b"my_new_app:MNA Shell").hexdigest()[:16]
	shell_block = build_shell()
	write_json("components", "MNA Shell", component(shell_id, "MNA Shell", shell_block))

	# Registers the heading font with Builder, so its editor canvas and the
	# published page both load it (a CSS @font-face would reach only the page).
	write_json(
		"fonts",
		"newsreader",
		{
			"doctype": "User Font",
			"font_file": "/assets/my_new_app/builder_assets/fonts/Newsreader-Regular.woff2",
			"font_name": "Newsreader",
			"name": "Newsreader",
		},
	)

	blocks = build_search(shell_id, shell_block)
	write_json(
		"pages",
		"mna-search",
		page(
			"mna-search",
			"Search",
			"search",
			blocks,
			["MNA Styles", "MNA Shell", "MNA Search"],
			SEARCH_DATA_SCRIPT,
		),
	)
	print(f"Wrote Builder files to {OUT}")


if __name__ == "__main__":
	main()
