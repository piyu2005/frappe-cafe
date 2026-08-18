app_name = "my_new_app"
app_title = "Frappe Cafe"
app_publisher = "Priyanshi"
app_description = "project"
app_email = "hodagepriyanshi@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "my_new_app",
# 		"logo": "/assets/my_new_app/logo.png",
# 		"title": "My New App",
# 		"route": "/my_new_app",
# 		"has_permission": "my_new_app.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/my_new_app/css/my_new_app.css"
# app_include_js = "/assets/my_new_app/js/my_new_app.js"

# include js, css files in header of web template
# web_include_css = "/assets/my_new_app/css/my_new_app.css"
# web_include_js = "/assets/my_new_app/js/my_new_app.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "my_new_app/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# The frontend is a Vue SPA — every sub-path (e.g. /frontend/settings,
# /frontend/write/abc123) needs to resolve to the same www/frontend.html
# entry point so Vue Router can take over client-side, not 404 on a direct
# link or a page refresh.
website_route_rules = [
	{"from_route": "/frontend/<path:app_path>", "to_route": "frontend"},
]

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "my_new_app/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# Every real account here is a Website User with no role beyond "All"/"Guest"
# (see my_new_app/chat.py's _attachment_url comment for why — granting
# System User would also hand out desk/backend access). Without this, login
# falls through Frappe's default resolution with nothing configured and
# lands on /desk — the backend admin UI, not this app. Administrator/System
# User accounts are unaffected: frappe/www/login.py only consults
# role_home_page for user_type == "Website User", they're hardcoded to
# /desk regardless.
role_home_page = {
	"All": "frontend",
}

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "my_new_app.utils.jinja_methods",
# 	"filters": "my_new_app.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "my_new_app.install.before_install"
# after_install = "my_new_app.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "my_new_app.uninstall.before_uninstall"
# after_uninstall = "my_new_app.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "my_new_app.utils.before_app_install"
# after_app_install = "my_new_app.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "my_new_app.utils.before_app_uninstall"
# after_app_uninstall = "my_new_app.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "my_new_app.build.after_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "my_new_app.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

permission_query_conditions = {
	"Post": "my_new_app.my_new_app.doctype.post.post.get_permission_query_conditions",
}

has_permission = {
	"Post": "my_new_app.my_new_app.doctype.post.post.has_permission",
}

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"my_new_app.tasks.all"
# 	],
# 	"daily": [
# 		"my_new_app.tasks.daily"
# 	],
# 	"hourly": [
# 		"my_new_app.tasks.hourly"
# 	],
# 	"weekly": [
# 		"my_new_app.tasks.weekly"
# 	],
# 	"monthly": [
# 		"my_new_app.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "my_new_app.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "my_new_app.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "my_new_app.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "my_new_app.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["my_new_app.utils.before_request"]
# after_request = ["my_new_app.utils.after_request"]

# Job Events
# ----------
# before_job = ["my_new_app.utils.before_job"]
# after_job = ["my_new_app.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"my_new_app.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

after_migrate = ["my_new_app.setup.after_migrate"]

