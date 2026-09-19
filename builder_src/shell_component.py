"""The app shell (rail, mobile bottom bar, logo menu) as a Builder component."""

from blocks import DIALOG_SHADOW, INK, MUTED, OUTLINE, SURFACE_1, block, icon


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
	# The rail itself stretches the full height of the page (background and
	# border). Its content sticks to the top of the window while the page scrolls.
	rail = block(
		"nav",
		"Rail",
		["mna-rail"],
		attrs={"aria-label": "Main"},
		styles={
			"flexShrink": "0",
			"width": "50px",
			"backgroundColor": SURFACE_1,
			"borderRight": f"1px solid {OUTLINE}",
		},
		children=[
			block(
				"div",
				"Rail content",
				styles={
					"position": "sticky",
					"top": "0",
					"display": "flex",
					"flexDirection": "column",
					"alignItems": "center",
					"gap": "12px",
					"height": "100vh",
					"padding": "10px 11px 12px",
				},
				children=[logo] + [rail_item(*item) for item in NAV_ITEMS],
			)
		],
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
