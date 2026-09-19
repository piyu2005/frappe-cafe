"""The app shell (rail, mobile bottom bar, logo menu) as a Builder component.

The whole shell is ONE block that holds ready-made HTML. As separate blocks it
was 32 blocks, and Builder's per-block render cost (about 1-2 ms each, on every
request, for every page) made it a big part of each page's server time. To
change the shell, edit this file and run generate.py, or edit the block's HTML
in Builder's editor.
"""

from blocks import DIALOG_SHADOW, INK, MUTED, OUTLINE, SURFACE_1, block, html_el, svg

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
LOGO_STYLES = {
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
}
# The rail itself stretches the full height of the page (background and border).
# Its content sticks to the top of the window while the page scrolls.
RAIL_STYLES = {
	"flexShrink": "0",
	"width": "50px",
	"backgroundColor": SURFACE_1,
	"borderRight": f"1px solid {OUTLINE}",
}
RAIL_CONTENT_STYLES = {
	"position": "sticky",
	"top": "0",
	"display": "flex",
	"flexDirection": "column",
	"alignItems": "center",
	"gap": "12px",
	"height": "100vh",
	"padding": "10px 11px 12px",
}
MENU_STYLES = {
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
}


def badge():
	return html_el("span", ["mna-badge"], {"data-badge": "messages"}, BADGE_STYLES)


def rail_item(key, label, href, icon_name):
	children = [svg(icon_name, 16)]
	if key == "messages":
		children.append(badge())
	return html_el(
		"a",
		["mna-rail-item"],
		{"href": href, "title": label, "aria-label": label, "data-nav": key},
		RAIL_ITEM_STYLES,
		children,
	)


def tab_item(key, label, href, icon_name):
	"""Mobile bottom-bar tab. Its look is in styles.css, under the 768px media
	query, because Builder has no breakpoint at that width."""
	children = [svg(icon_name, 24, "inherit")]
	if key == "messages":
		children.append(badge())
	return html_el(
		"a",
		["mna-tab"],
		{"href": href, "aria-label": label, "data-nav": key},
		None,
		children,
	)


def menu_item(tag, attrs, icon_name, label):
	return html_el(
		tag,
		["mna-menu-item"],
		{**attrs, "role": "menuitem"},
		MENU_ITEM_STYLES,
		[svg(icon_name, 16, MUTED), html_el("span", text=label)],
	)


def build_shell_html():
	logo = html_el(
		"button",
		["mna-logo"],
		{"id": "mna-logo", "type": "button", "aria-label": "Cafe menu", "aria-haspopup": "menu"},
		LOGO_STYLES,
		[svg("feather", 16)],
	)
	rail = html_el(
		"nav",
		["mna-rail"],
		{"aria-label": "Main"},
		RAIL_STYLES,
		[
			html_el(
				"div",
				["mna-rail-content"],
				None,
				RAIL_CONTENT_STYLES,
				[logo] + [rail_item(*item) for item in NAV_ITEMS],
			)
		],
	)
	bottom_nav = html_el(
		"nav",
		["mna-bottom-nav"],
		{"aria-label": "Main"},
		{"display": "none"},
		[tab_item(*item) for item in TAB_ITEMS],
	)
	menu = html_el(
		"div",
		["mna-menu"],
		{"id": "mna-menu", "role": "menu"},
		MENU_STYLES,
		[
			menu_item("a", {"href": "/settings"}, "settings", "Settings"),
			menu_item("button", {"id": "mna-logout", "type": "button"}, "log-out", "Logout"),
		],
	)
	return rail + bottom_nav + menu


def build_shell():
	# display: contents keeps this wrapper out of the page layout: the rail and
	# main column stay direct flex children of the app container.
	return block(
		"div",
		"Shell",
		["mna-shell"],
		html=build_shell_html(),
		styles={"display": "contents"},
	)
