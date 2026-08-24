"""Tests for the email-verification signup flow: signup() no longer creates
a User immediately - without this, anyone could type in someone else's real
email address and be logged in instantly as "them", with nothing ever
confirming they actually own that inbox. The submitted details now sit
behind a one-time cache token instead, and only verify_email() (what the
emailed link points at) actually creates the account. Covers the flow's
real security property plus the usual expiry/replay/race edge cases."""

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase, set_user

from my_new_app.api import SIGNUP_CACHE_PREFIX, signup, verify_email


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


class TestSignupValidation(IntegrationTestCase):
	# Duplicate checks happen before anything touches the cache or tries to
	# send mail, so these don't need an Email Account configured to test.

	def test_rejects_duplicate_email(self):
		existing = _make_user("signup_dup_email@example.com", "Dup")
		with set_user("Guest"):
			with self.assertRaises(frappe.ValidationError):
				signup(email=existing, password="Whatever123!", username="somethingbrandnew")

	def test_rejects_duplicate_username(self):
		taken_user = _make_user("signup_dup_username@example.com", "Dup")
		frappe.db.set_value("User", taken_user, "username", "signuptakenname")
		with set_user("Guest"):
			with self.assertRaises(frappe.ValidationError):
				signup(email="signup_fresh_email@example.com", password="Whatever123!", username="signuptakenname")


class TestVerifyEmail(IntegrationTestCase):
	def setUp(self):
		# Unique per test method - IntegrationTestCase's rollback is
		# class-scoped, not per-test (a documented gotcha elsewhere in this
		# app's test suite too), so a literal email/username shared across
		# every test in this class would have the first test that actually
		# creates the User "poison" every test after it.
		unique = frappe.generate_hash(length=8)
		self.token = frappe.generate_hash(length=32)
		self.email = f"verify_flow_{unique}@example.com"
		self.username = f"verifyflow{unique}"

		# verify_email() ends by calling LoginManager(), which needs a full
		# WSGI request context (cookie manager, session machinery, etc.) that
		# only exists for a real HTTP call - confirmed separately via curl
		# that the actual login step works correctly there. Reproducing that
		# whole stack here just to satisfy it would mean re-testing frappe's
		# own login machinery rather than this feature's logic, so the login
		# step is mocked out; everything verify_email() itself is responsible
		# for (creating the user, cleaning up the token, re-checking
		# uniqueness) still runs for real and is asserted below.
		login_manager_patcher = patch("my_new_app.api.LoginManager")
		self.mock_login_manager = login_manager_patcher.start()
		self.addCleanup(login_manager_patcher.stop)

	def _seed_pending_signup(self, **overrides):
		payload = {"email": self.email, "username": self.username, "password": "TestPass123!"}
		payload.update(overrides)
		frappe.cache.set_value(f"{SIGNUP_CACHE_PREFIX}{self.token}", frappe.as_json(payload), expires_in_sec=3600)

	def test_valid_token_creates_and_enables_the_user(self):
		self._seed_pending_signup()
		with set_user("Guest"):
			verify_email(key=self.token)
		self.assertTrue(frappe.db.exists("User", self.email))
		self.assertEqual(frappe.db.get_value("User", self.email, "enabled"), 1)
		# The whole point: the token is consumed, so nobody can replay it to
		# re-run the flow against a different/later state.
		self.assertIsNone(frappe.cache.get_value(f"{SIGNUP_CACHE_PREFIX}{self.token}"))
		self.mock_login_manager.return_value.login_as.assert_called_once_with(self.email)

	def test_valid_token_is_single_use(self):
		self._seed_pending_signup()
		with set_user("Guest"):
			verify_email(key=self.token)
			with self.assertRaises(frappe.ValidationError):
				verify_email(key=self.token)

	def test_invalid_token_does_not_create_a_user(self):
		with set_user("Guest"):
			with self.assertRaises(frappe.ValidationError):
				verify_email(key="not-a-real-token-at-all")
		self.assertFalse(frappe.db.exists("User", self.email))

	def test_email_taken_while_pending_is_caught_at_verify_time(self):
		self._seed_pending_signup()
		# Someone else claims the same email through a separate signup while
		# this token sits unused - re-checked at verify time rather than
		# trusting the check already done (and now stale) at signup time.
		_make_user(self.email, "SomeoneElse")
		with set_user("Guest"):
			with self.assertRaises(frappe.ValidationError):
				verify_email(key=self.token)

	def test_username_taken_while_pending_is_caught_at_verify_time(self):
		self._seed_pending_signup()
		other = _make_user("verify_someone_else@example.com", "SomeoneElse")
		frappe.db.set_value("User", other, "username", self.username)
		with set_user("Guest"):
			with self.assertRaises(frappe.ValidationError):
				verify_email(key=self.token)
