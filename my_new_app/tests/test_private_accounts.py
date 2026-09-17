"""Private-account content gating: Education, Work History and Posts should
only be visible to the profile owner or an approved follower once
`is_private` is set - a pending follow request doesn't count as approved,
and the header (name/avatar/headline/bio) is intentionally never gated, so
it isn't covered here."""

import frappe
from frappe.tests import IntegrationTestCase, set_user

from my_new_app.api import get_post, get_profile, list_profile_posts


def _make_user(email, first_name, is_private=0):
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": first_name,
				"send_welcome_email": 0,
				"user_type": "Website User",
				"is_private": is_private,
			}
		).insert(ignore_permissions=True)
	return email


class TestPrivateAccountGating(IntegrationTestCase):
	def setUp(self):
		self.owner = _make_user("priv_owner@example.com", "PrivOwner", is_private=1)
		self.follower = _make_user("priv_follower@example.com", "PrivFollower")
		self.requester = _make_user("priv_requester@example.com", "PrivRequester")
		self.stranger = _make_user("priv_stranger@example.com", "PrivStranger")

		with set_user(self.owner):
			frappe.get_doc({"doctype": "Education Entry", "school": "Test University"}).insert(
				ignore_permissions=True
			)
			frappe.get_doc({"doctype": "Work Entry", "company": "Test Corp"}).insert(ignore_permissions=True)
			self.post_name = frappe.get_doc(
				{"doctype": "Post", "content": "<p>hello</p>", "status": "Published", "post_type": "Blog"}
			).insert(ignore_permissions=True).name

		frappe.get_doc(
			{
				"doctype": "Subscription",
				"reference_doctype": "User",
				"reference_name": self.owner,
				"subscriber": self.follower,
			}
		).insert(ignore_permissions=True)
		frappe.get_doc({"doctype": "Follow Request", "to_user": self.owner, "from_user": self.requester}).insert(
			ignore_permissions=True
		)

	# setUp() reruns before every test in this class (IntegrationTestCase's
	# rollback is class-scoped, not per-test - same gotcha documented in
	# test_signup_verification.py and test_permissions.py), so each of these
	# two tests checks for its own entry by identity rather than an exact
	# count, since earlier tests' setUp() calls leave their own entries
	# lying around too.
	def test_owner_sees_own_content(self):
		with set_user(self.owner):
			profile = get_profile(self.owner)
			posts = list_profile_posts(self.owner)
		self.assertTrue(any(e.school == "Test University" for e in profile.education))
		self.assertTrue(any(w.company == "Test Corp" for w in profile.work))
		self.assertTrue(any(p.name == self.post_name for p in posts))

	def test_approved_follower_sees_content(self):
		with set_user(self.follower):
			profile = get_profile(self.owner)
			posts = list_profile_posts(self.owner)
			post = get_post(self.post_name)
		self.assertTrue(any(e.school == "Test University" for e in profile.education))
		self.assertTrue(any(w.company == "Test Corp" for w in profile.work))
		self.assertTrue(any(p.name == self.post_name for p in posts))
		self.assertEqual(post.name, self.post_name)

	def test_stranger_is_gated(self):
		with set_user(self.stranger):
			profile = get_profile(self.owner)
			posts = list_profile_posts(self.owner)
		self.assertEqual(profile.education, [])
		self.assertEqual(profile.work, [])
		self.assertEqual(posts, [])
		with set_user(self.stranger):
			with self.assertRaises(frappe.PermissionError):
				get_post(self.post_name)

	def test_pending_requester_is_gated(self):
		with set_user(self.requester):
			profile = get_profile(self.owner)
			posts = list_profile_posts(self.owner)
		self.assertEqual(profile.education, [])
		self.assertEqual(profile.work, [])
		self.assertEqual(posts, [])
		with set_user(self.requester):
			with self.assertRaises(frappe.PermissionError):
				get_post(self.post_name)

	def test_non_private_account_is_never_gated(self):
		public_user = _make_user("priv_public@example.com", "PrivPublic")
		with set_user(public_user):
			doc = frappe.get_doc({"doctype": "Education Entry", "school": "Open University"})
			doc.insert(ignore_permissions=True)
			post_name = frappe.get_doc(
				{"doctype": "Post", "content": "<p>hi</p>", "status": "Published", "post_type": "Blog"}
			).insert(ignore_permissions=True).name

		with set_user(self.stranger):
			profile = get_profile(public_user)
			posts = list_profile_posts(public_user)
			post = get_post(post_name)
		self.assertEqual(len(profile.education), 1)
		self.assertEqual(len(posts), 1)
		self.assertEqual(post.name, post_name)
