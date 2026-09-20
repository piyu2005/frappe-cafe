import frappe
from frappe.tests import IntegrationTestCase


class TestSmoke(IntegrationTestCase):
	def test_app_is_installed(self):
		self.assertIn("my_new_app", frappe.get_installed_apps())
