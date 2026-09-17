"""Ownership/IDOR protection — can a user read, edit, or delete another
user's data through the doctype permission system? These mirror the manual
checks done by hand during development; here they run automatically and
can't silently regress."""

import frappe
from frappe.tests import IntegrationTestCase, set_user

from my_new_app.api import add_education, delete_education, delete_work, update_education, update_work


def _make_user(email, first_name):
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": first_name,
				"send_welcome_email": 0,
				"user_type": "Website User",
			}
		).insert(ignore_permissions=True)
	return email


class TestEducationEntryPermissions(IntegrationTestCase):
	def setUp(self):
		self.owner = _make_user("perm_owner@example.com", "Owner")
		self.other = _make_user("perm_other@example.com", "Other")
		with set_user(self.owner):
			self.entry = add_education(school="Test University", degree="BSc")

	def test_owner_can_update_own_entry(self):
		with set_user(self.owner):
			result = update_education(self.entry["name"], school="Updated University")
		self.assertEqual(result["school"], "Updated University")

	def test_other_user_cannot_update_entry(self):
		with set_user(self.other):
			with self.assertRaises(frappe.PermissionError):
				update_education(self.entry["name"], school="Hacked")

	def test_other_user_cannot_delete_entry(self):
		with set_user(self.other):
			with self.assertRaises(frappe.PermissionError):
				delete_education(self.entry["name"])
		# still there afterwards
		self.assertTrue(frappe.db.exists("Education Entry", self.entry["name"]))

	def test_anyone_can_read_entry(self):
		# Education entries are shown on a public profile page — read access
		# is intentionally open, only write/delete are owner-restricted.
		with set_user(self.other):
			doc = frappe.get_doc("Education Entry", self.entry["name"])
			self.assertEqual(doc.school, "Test University")


class TestWorkEntryPermissions(IntegrationTestCase):
	def setUp(self):
		self.owner = _make_user("perm_owner2@example.com", "Owner2")
		self.other = _make_user("perm_other2@example.com", "Other2")
		from my_new_app.api import add_work

		with set_user(self.owner):
			self.entry = add_work(company="Test Corp", title="Engineer")

	def test_other_user_cannot_update_entry(self):
		with set_user(self.other):
			with self.assertRaises(frappe.PermissionError):
				update_work(self.entry["name"], company="Hacked Corp")

	def test_other_user_cannot_delete_entry(self):
		with set_user(self.other):
			with self.assertRaises(frappe.PermissionError):
				delete_work(self.entry["name"])


class TestPostVisibility(IntegrationTestCase):
	def setUp(self):
		self.author = _make_user("perm_author@example.com", "Author")
		self.reader = _make_user("perm_reader@example.com", "Reader")

	def _make_post(self, status):
		with set_user(self.author):
			doc = frappe.get_doc(
				{"doctype": "Post", "content": "<p>hello</p>", "status": status, "post_type": "Blog"}
			)
			doc.insert(ignore_permissions=True)
			return doc.name

	def test_published_post_visible_to_others(self):
		name = self._make_post("Published")
		with set_user(self.reader):
			self.assertTrue(frappe.has_permission("Post", "read", frappe.get_doc("Post", name)))

	def test_draft_post_not_visible_to_others(self):
		name = self._make_post("Draft")
		with set_user(self.reader):
			self.assertFalse(frappe.has_permission("Post", "read", frappe.get_doc("Post", name)))

	def test_archived_post_not_visible_to_others(self):
		name = self._make_post("Archived")
		with set_user(self.reader):
			self.assertFalse(frappe.has_permission("Post", "read", frappe.get_doc("Post", name)))

	def test_draft_post_visible_to_author(self):
		name = self._make_post("Draft")
		with set_user(self.author):
			self.assertTrue(frappe.has_permission("Post", "read", frappe.get_doc("Post", name)))

	def test_other_user_cannot_edit_published_post(self):
		name = self._make_post("Published")
		with set_user(self.reader):
			doc = frappe.get_doc("Post", name)
			self.assertFalse(doc.has_permission("write"))


class TestPublicationMemberPermissions(IntegrationTestCase):
	"""list_publication_members reveals pending invites (who's been invited,
	and as what role) - not something a stranger to the publication should
	be able to see just by knowing its handle."""

	def setUp(self):
		# Unique per test method - setUp() reruns before every test in this
		# class, but IntegrationTestCase's rollback is class-scoped, not
		# per-test (same gotcha documented in test_signup_verification.py), so
		# a literal handle here would have the first test's setUp "poison"
		# every test after it with an "already taken" error.
		unique = frappe.generate_hash(length=8)
		self.admin = _make_user("perm_pub_admin@example.com", "PubAdmin")
		self.outsider = _make_user("perm_pub_outsider@example.com", "PubOutsider")
		with set_user(self.admin):
			from my_new_app.api import create_publication

			self.handle = create_publication(title="Perm Test Pub", handle=f"permtestpub{unique}")["handle"]

	def test_non_member_cannot_list_members(self):
		from my_new_app.api import list_publication_members

		with set_user(self.outsider):
			with self.assertRaises(frappe.PermissionError):
				list_publication_members(self.handle)

	def test_admin_can_list_members(self):
		from my_new_app.api import list_publication_members

		with set_user(self.admin):
			result = list_publication_members(self.handle)
		self.assertEqual(len(result["editors"]), 1)


class TestFollowUserBlocking(IntegrationTestCase):
	def setUp(self):
		self.a = _make_user("perm_follow_a@example.com", "FollowA")
		self.b = _make_user("perm_follow_b@example.com", "FollowB")

	def test_blocked_user_cannot_follow(self):
		from my_new_app.chat import block_user
		from my_new_app.follow import follow_user

		with set_user(self.a):
			block_user(self.b)
		with set_user(self.b):
			with self.assertRaises(frappe.ValidationError):
				follow_user(self.a)
		self.assertFalse(frappe.db.exists("Subscription", {"reference_doctype": "User", "reference_name": self.a, "subscriber": self.b}))

	def test_unblocked_user_can_follow_again(self):
		from my_new_app.chat import block_user, unblock_user
		from my_new_app.follow import follow_user

		with set_user(self.a):
			block_user(self.b)
			unblock_user(self.b)
		with set_user(self.b):
			follow_user(self.a)
		self.assertTrue(frappe.db.exists("Subscription", {"reference_doctype": "User", "reference_name": self.a, "subscriber": self.b}))


class TestNotificationOwnership(IntegrationTestCase):
	def setUp(self):
		self.owner = _make_user("perm_notif_owner@example.com", "NotifOwner")
		self.other = _make_user("perm_notif_other@example.com", "NotifOther")
		self.notif_name = frappe.get_doc(
			{
				"doctype": "App Notification",
				"recipient": self.owner,
				"type": "New Follower",
				"message": "test",
			}
		).insert(ignore_permissions=True).name

	def test_other_user_cannot_mark_someone_elses_notification_read(self):
		from my_new_app.follow import mark_notification_read

		with set_user(self.other):
			mark_notification_read(self.notif_name)
		self.assertEqual(frappe.db.get_value("App Notification", self.notif_name, "is_read"), 0)

	def test_owner_can_mark_their_own_notification_read(self):
		from my_new_app.follow import mark_notification_read

		with set_user(self.owner):
			mark_notification_read(self.notif_name)
		self.assertEqual(frappe.db.get_value("App Notification", self.notif_name, "is_read"), 1)
