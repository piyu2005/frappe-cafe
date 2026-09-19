"""The frame every page shares: shell, header with breadcrumbs, scroll area and
a centered container."""

from blocks import INK, INK_BLACK, MUTED, OUTLINE, block, html_el, instance_of, raw_block, svg


def crumb_link(label, href, styles=None, name=None):
	return block("a", name, text=label, attrs={"href": href}, styles=styles)


def crumb_separator():
	return block(
		"span",
		"Separator",
		classes=["sep"],
		text="/",
		styles={"color": "#999999", "fontSize": "14px", "fontWeight": "420", "letterSpacing": "0.02em"},
	)


def crumb_current(label, name=None):
	return block("span", name, classes=["current"], text=label, styles={"color": INK_BLACK})


def page_header(crumbs):
	return block(
		"header",
		"Header",
		["mna-header"],
		styles={
			"position": "sticky",
			"top": "0",
			"zIndex": "10",
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
				children=crumbs,
			),
			raw_block(
				"New Post",
				html_el(
					"a",
					["mna-btn", "mna-btn-solid"],
					{"href": "/write"},
					{
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
					[svg("plus", 16), html_el("span", text="New Post")],
				),
				styles={"display": "flex"},
			),
		],
	)


def page_layout(shell_id, shell_block, crumbs, content, max_width, mobile_header=None):
	"""The page body: `crumbs` go in the header and `content` in the container,
	which is `max_width` wide including its 20px side padding. A page can add a
	`mobile_header`, a top bar that only shows on a phone."""
	container = block(
		"section",
		"Container",
		["mna-container"],
		styles={"width": "100%", "maxWidth": max_width, "margin": "0 auto", "padding": "32px 20px"},
		children=content,
	)
	main = block(
		"div",
		"Main",
		["mna-main"],
		styles={"display": "flex", "flexGrow": "1", "flexDirection": "column", "minWidth": "0"},
		children=[
			*([mobile_header] if mobile_header else []),
			page_header(crumbs),
			block(
				"div",
				"Scroll area",
				["mna-scroll"],
				styles={"flexGrow": "1"},
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
			# The page grows with its content and the document scrolls, so the
			# editor canvas shows the whole page. The rail and header are sticky.
			"minHeight": "100vh",
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
