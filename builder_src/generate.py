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
import json
import re
import shutil
from datetime import datetime
from pathlib import Path

SRC = Path(__file__).resolve().parent
REPO = SRC.parent
APP = REPO / "my_new_app"
OUT = APP / "builder_files"
FONTS_OUT = APP / "public" / "builder_assets" / "fonts"
FONT_FILES = {REPO / "frontend" / "src" / "assets" / "Newsreader" / "Newsreader-Regular.woff2"}

NOW = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
def slug(name):
	return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")

from profile_page import (  # noqa: E402
	PROFILE_DATA_SCRIPT,
	PROFILE_REDIRECT_SCRIPT,
	build_profile,
	build_profile_redirect,
)
from post_page import POST_DATA_SCRIPT, build_post_page  # noqa: E402
from posts_page import POSTS_DATA_SCRIPT, build_posts_page  # noqa: E402
from search_page import SEARCH_DATA_SCRIPT, build_search  # noqa: E402
from shell_component import build_shell  # noqa: E402


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


def page(name, title, route, blocks, script_names, data_script, dynamic=False):
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
		"dynamic_route": 1 if dynamic else 0,
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


TIMESTAMPS = ("creation", "modified", "published_at")


def without_timestamps(doc):
	return {key: value for key, value in doc.items() if key not in TIMESTAMPS}


def read_existing():
	"""The files from the last run, so an unchanged file keeps its timestamps."""
	if not OUT.exists():
		return {}
	return {path: json.loads(path.read_text()) for path in OUT.rglob("*.json")}


EXISTING = {}


def write_json(kind, name, doc):
	folder = OUT / kind / slug(name)
	folder.mkdir(parents=True, exist_ok=True)
	path = folder / f"{slug(name)}.json"
	old = EXISTING.get(path)
	if old is not None and without_timestamps(old) == without_timestamps(doc):
		doc = old  # nothing changed: keep the timestamps, so git and Builder see no change
	path.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")


def main():
	EXISTING.update(read_existing())
	if OUT.exists():
		shutil.rmtree(OUT)

	FONTS_OUT.mkdir(parents=True, exist_ok=True)
	for font in FONT_FILES:
		shutil.copy(font, FONTS_OUT / font.name)

	scripts = [
		("MNA Styles", "CSS", "styles.css"),
		("MNA UI", "JavaScript", "ui.js"),
		("MNA Shell", "JavaScript", "shell.js"),
		("MNA Search", "JavaScript", "search.js"),
		("MNA Profile", "JavaScript", "profile.js"),
		("MNA Posts", "JavaScript", "posts.js"),
		("MNA Post", "JavaScript", "post.js"),
	]
	for index, (name, kind, filename) in enumerate(scripts, start=1):
		write_json("client_scripts", name, client_script(name, kind, (SRC / filename).read_text(), index))

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

	shared = ["MNA Styles", "MNA UI", "MNA Shell"]
	pages = [
		("mna-search", "Search", "search", build_search, shared + ["MNA Search"], SEARCH_DATA_SCRIPT, False),
		("mna-profile", "Profile", "profile/:username", build_profile, shared + ["MNA Profile"], PROFILE_DATA_SCRIPT, True),
		("mna-profile-self", "My profile", "profile", build_profile_redirect, ["MNA Styles"], PROFILE_REDIRECT_SCRIPT, False),
		("mna-profile-posts", "Profile posts", "profile/:username/posts", build_posts_page, shared + ["MNA Posts"], POSTS_DATA_SCRIPT, True),
		("mna-post", "Post", "posts/:post_id", build_post_page, shared + ["MNA Post"], POST_DATA_SCRIPT, True),
	]
	for name, title, route, builder, script_names, data_script, dynamic in pages:
		blocks = builder(shell_id, shell_block)
		write_json("pages", name, page(name, title, route, blocks, script_names, data_script, dynamic))
	print(f"Wrote Builder files to {OUT}")


if __name__ == "__main__":
	main()
