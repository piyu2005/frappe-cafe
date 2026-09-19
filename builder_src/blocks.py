"""Helpers that build Builder blocks. Shared by the shell and every page."""

import html as htmllib
import random
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LUCIDE = REPO / "frontend" / "node_modules" / "lucide-static" / "icons"

_ids = random.Random("my_new_app.builder")


def block_id():
	return "".join(_ids.choices("0123456789abcdefghijklmnopqrstuvwxyz", k=9))


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


def bind(key, prop, kind):
	"""A binding of a block property to a key of the data script's data. Inside a
	repeater the key is looked up on the current item."""
	return {"comesFrom": "dataScript", "key": key, "property": prop, "type": kind}
