import frappe
from frappe.auth import LoginManager
from frappe.rate_limiter import rate_limit


SIGNUP_CACHE_PREFIX = "pending_signup:"
SIGNUP_LINK_EXPIRY_SEC = 24 * 60 * 60


def _create_verified_user(email, username, password):
	user = frappe.get_doc(
		{
			"doctype": "User",
			"email": email,
			"first_name": username,
			"username": username,
			"enabled": 1,
			"user_type": "Website User",
			"send_welcome_email": 0,
			"new_password": password,
		}
	)
	user.flags.ignore_permissions = True
	user.insert()
	return user


@frappe.whitelist(allow_guest=True)
# Public, so without this an unauthenticated script could hammer it to
# enumerate registered emails (via the "already exists" error) or queue up
# mass account-creation attempts. IP-based, matching frappe core's own
# guest-facing endpoints (e.g. User.clear_session).
@rate_limit(limit=10, seconds=60 * 60)
def signup(email, password, username):
	email = email.strip().lower()
	if frappe.db.exists("User", email):
		frappe.throw("An account with this email already exists. Please log in instead.")

	username = username.strip()
	if frappe.db.exists("User", {"username": username}):
		frappe.throw("This username is already taken. Please choose another.")

	# No User is created yet - anyone could otherwise type in someone else's
	# real email address and be logged in immediately as "them", with nothing
	# ever confirming they actually own that inbox. The submitted details sit
	# in cache under a one-time token until the emailed link proves it;
	# _create_verified_user() (verify_email, below) is the only thing that
	# ever actually inserts the User doc.
	token = frappe.generate_hash(length=32)
	frappe.cache.set_value(
		f"{SIGNUP_CACHE_PREFIX}{token}",
		frappe.as_json({"email": email, "username": username, "password": password}),
		expires_in_sec=SIGNUP_LINK_EXPIRY_SEC,
	)

	verify_url = frappe.utils.get_url(f"/frontend/verify-email?key={token}")
	frappe.sendmail(
		recipients=email,
		subject="Verify your email for Frappe Cafe",
		message=f"""
			<p>Welcome to Frappe Cafe! Click the link below to verify your email and finish creating your account.</p>
			<p><a href="{verify_url}">Verify your email</a></p>
			<p>This link expires in 24 hours. If you didn't try to sign up, you can ignore this email.</p>
		""",
		now=True,
	)
	return "success"


@frappe.whitelist(allow_guest=True)
# Token is a 32-char cryptographically random hash - not realistically
# guessable - but rate-limited anyway as cheap defense-in-depth, matching
# frappe core's own treatment of its equivalent key-based endpoint
# (frappe.www.login.login_via_key).
@rate_limit(limit=20, seconds=60 * 60)
def verify_email(key):
	cache_key = f"{SIGNUP_CACHE_PREFIX}{key}"
	cached = frappe.cache.get_value(cache_key)
	if not cached:
		frappe.throw("This verification link is invalid or has expired. Please sign up again.")

	data = frappe.parse_json(cached)

	# Re-check uniqueness rather than trusting the check already done at
	# signup time - someone else could have registered (and verified) the
	# same email or username while this link sat unused.
	if frappe.db.exists("User", data["email"]):
		frappe.cache.delete_value(cache_key)
		frappe.throw("An account with this email already exists. Please log in instead.")
	if frappe.db.exists("User", {"username": data["username"]}):
		frappe.cache.delete_value(cache_key)
		frappe.throw("This username was taken while your verification was pending. Please sign up again with a different username.")

	_create_verified_user(data["email"], data["username"], data["password"])
	frappe.cache.delete_value(cache_key)

	login_manager = LoginManager()
	login_manager.login_as(data["email"])
	return "success"


@frappe.whitelist(allow_guest=True)
def get_google_login_url(redirect_to="/frontend"):
	if not frappe.db.exists(
		"Social Login Key", {"social_login_provider": "Google", "enable_social_login": 1}
	):
		return None
	from frappe.utils.oauth import get_oauth2_authorize_url

	return get_oauth2_authorize_url("google", redirect_to)


def _subscriber_count(reference_type, reference_name):
	return frappe.db.count(
		"Subscription", {"reference_type": reference_type, "reference_name": reference_name}
	)


def _subscribed_by_me(reference_type, reference_name):
	if frappe.session.user == "Guest":
		return False
	return bool(
		frappe.db.exists(
			"Subscription",
			{
				"reference_type": reference_type,
				"reference_name": reference_name,
				"subscriber": frappe.session.user,
			},
		)
	)


@frappe.whitelist()
def toggle_subscribe(reference_type, reference_name):
	user = frappe.session.user
	if user == "Guest":
		frappe.throw("Not permitted", frappe.PermissionError)

	existing = frappe.db.exists(
		"Subscription",
		{"reference_type": reference_type, "reference_name": reference_name, "subscriber": user},
	)
	if existing:
		frappe.delete_doc("Subscription", existing, ignore_permissions=True)
		subscribed = False
	else:
		sub = frappe.get_doc(
			{
				"doctype": "Subscription",
				"reference_type": reference_type,
				"reference_name": reference_name,
			}
		)
		sub.flags.ignore_permissions = True
		sub.insert()
		subscribed = True

	return {"subscribed": subscribed, "count": _subscriber_count(reference_type, reference_name)}


@frappe.whitelist()
def get_profile(user=None):
	user = user or frappe.session.user
	if user == "Guest":
		frappe.throw("Not permitted", frappe.PermissionError)

	profile = frappe.db.get_value(
		"User",
		user,
		[
			"name",
			"full_name",
			"username",
			"user_image",
			"bio",
			"headline",
			"location",
			"job_title",
			"company",
			"is_private",
			"creation",
		],
		as_dict=True,
	)
	if not profile:
		frappe.throw("User not found")

	from my_new_app.follow import get_follow_state

	profile.username = profile.username or profile.name.split("@")[0]
	profile.post_count = frappe.db.count("Post", {"author": user, "status": "Published"})
	profile.follower_count = _subscriber_count("User", user)
	follow_state = get_follow_state(user) if frappe.session.user != "Guest" else {"following": False, "pending": False}
	profile.following_by_me = follow_state["following"]
	profile.follow_pending = follow_state["pending"]
	profile.education = frappe.db.get_all(
		"Education Entry",
		filters={"user": user},
		fields=["name", "school", "degree", "field_of_study", "start_year", "end_year"],
		order_by="creation asc",
	)
	profile.work = frappe.db.get_all(
		"Work Entry",
		filters={"user": user},
		fields=["name", "company", "title", "start_date", "end_date", "description"],
		order_by="creation asc",
	)
	return profile


@frappe.whitelist()
def list_profile_posts(user=None, limit=3):
	user = user or frappe.session.user
	rows = frappe.db.get_all(
		"Post",
		filters={"author": user, "status": "Published"},
		fields=[
			"name",
			"title",
			"display_title",
			"content",
			"excerpt",
			"post_type",
			"cover_image",
			"attachment",
			"creation",
		],
		order_by="creation desc",
		limit_page_length=int(limit),
	)
	counts = {}
	if rows:
		for c in frappe.db.get_all(
			"Post Comment", filters={"post": ["in", [r.name for r in rows]]}, fields=["post"]
		):
			counts[c.post] = counts.get(c.post, 0) + 1
	for row in rows:
		row.comment_count = counts.get(row.name, 0)
	return rows


@frappe.whitelist()
def get_comment_counts(posts):
	if isinstance(posts, str):
		posts = frappe.parse_json(posts)
	if not posts:
		return {}
	counts = {}
	for c in frappe.db.get_all("Post Comment", filters={"post": ["in", posts]}, fields=["post"]):
		counts[c.post] = counts.get(c.post, 0) + 1
	return counts


@frappe.whitelist()
def change_password(old_password, new_password):
	user = frappe.session.user
	if user == "Guest":
		frappe.throw("Not permitted", frappe.PermissionError)

	from frappe.utils.password import check_password

	# Deliberately not re-raising frappe.AuthenticationError here: Frappe's
	# response middleware treats that exception type as a real login
	# failure and clears the session cookie regardless of where it came
	# from, which would silently log the user out just for mistyping their
	# current password. A plain ValidationError (the frappe.throw default)
	# surfaces the same message without that side effect.
	try:
		check_password(user, old_password)
	except frappe.AuthenticationError:
		frappe.throw("Current password is incorrect")

	doc = frappe.get_doc("User", user)
	doc.new_password = new_password
	doc.flags.ignore_permissions = True
	doc.save()
	return "success"


@frappe.whitelist()
def delete_account():
	# Paused: this only disabled the User rather than actually deleting it,
	# which left people locked out with no way back in on their own (a
	# disabled User blocks both a fresh signup and a fresh Google login with
	# the same email). Re-enable once there's a real account-deletion flow
	# (or at least a clear message on what "deleted" means) to replace this.
	frappe.throw("Account deletion is temporarily unavailable. Please contact support.")


@frappe.whitelist()
def list_people(query=None):
	filters = {"enabled": 1, "user_type": "Website User", "name": ["!=", "Guest"]}
	if query:
		filters["full_name"] = ["like", f"%{query}%"]

	return frappe.db.get_all(
		"User",
		filters=filters,
		fields=["name", "full_name", "user_image", "username"],
		order_by="full_name asc",
		limit_page_length=50,
	)


def _publication_role(publication, user=None):
	user = user or frappe.session.user
	return frappe.db.get_value("Publication Member", {"publication": publication, "user": user}, "role")


def _is_publication_admin(publication, user=None):
	return _publication_role(publication, user) == "Admin"


def _require_publication_admin(publication):
	if not _is_publication_admin(publication):
		frappe.throw("Only publication admins can do this", frappe.PermissionError)


@frappe.whitelist()
def create_publication(title, handle, description=None, website=None):
	handle = handle.strip().lower()
	if frappe.db.exists("Publication", handle):
		frappe.throw("That handle is already taken")

	pub = frappe.get_doc(
		{
			"doctype": "Publication",
			"title": title,
			"handle": handle,
			"description": description,
			"website": website,
		}
	)
	pub.flags.ignore_permissions = True
	pub.insert()

	member = frappe.get_doc(
		{
			"doctype": "Publication Member",
			"publication": handle,
			"user": frappe.session.user,
			"role": "Admin",
		}
	)
	member.flags.ignore_permissions = True
	member.insert()

	return {"handle": handle}


@frappe.whitelist()
def list_my_publications():
	rows = frappe.db.get_all(
		"Publication Member",
		filters={"user": frappe.session.user},
		fields=["publication", "role"],
	)
	for row in rows:
		row.title = frappe.db.get_value("Publication", row.publication, "title")
	return rows


@frappe.whitelist()
def leave_publication(handle):
	frappe.db.delete(
		"Publication Member", {"publication": handle, "user": frappe.session.user}
	)
	frappe.db.commit()
	return "success"


@frappe.whitelist()
def get_publication(handle):
	pub = frappe.db.get_value(
		"Publication",
		handle,
		["title", "handle", "description", "website", "logo"],
		as_dict=True,
	)
	if not pub:
		frappe.throw("Publication not found")

	members = frappe.db.get_all(
		"Publication Member",
		filters={"publication": handle},
		fields=["user", "role"],
	)

	# "Editors" here matches the Members page's grouping — Admins are editors
	# too, just badged distinctly, not a separate headline tier.
	pub.editor_count = len([m for m in members if m.role in ("Admin", "Editor")])
	pub.member_count = len(members)

	# Only the first 3 are ever shown here — enriching every member with 2
	# User lookups each (previously done for the whole list) meant a large
	# publication paid for names/avatars that were immediately thrown away.
	top_members = members[:3]
	if top_members:
		users_by_id = {
			u.name: u
			for u in frappe.db.get_all(
				"User", filters={"name": ["in", [m.user for m in top_members]]}, fields=["name", "full_name", "user_image"]
			)
		}
		for m in top_members:
			u = users_by_id.get(m.user)
			m.full_name = u.full_name if u else None
			m.user_image = u.user_image if u else None
	pub.members = top_members
	pub.subscriber_count = _subscriber_count("Publication", handle)
	pub.subscribed_by_me = _subscribed_by_me("Publication", handle)

	pub.posts = frappe.db.get_all(
		"Post",
		filters={"publication": handle, "status": "Published"},
		fields=["name", "title", "display_title", "content", "post_type", "attachment", "cover_image", "creation"],
		order_by="creation desc",
		limit_page_length=20,
	)
	return pub


@frappe.whitelist()
def list_publication_members(publication):
	if not frappe.db.exists("Publication", publication):
		frappe.throw("Publication not found")

	rows = frappe.db.get_all(
		"Publication Member",
		filters={"publication": publication},
		fields=["name", "user", "role", "creation"],
		order_by="creation asc",
	)
	pending_invites = frappe.db.get_all(
		"Publication Invite",
		filters={"publication": publication, "status": "Pending"},
		fields=["name", "invited_user", "role", "creation"],
		order_by="creation desc",
	)

	user_ids = list({r.user for r in rows} | {p.invited_user for p in pending_invites})
	users_by_id = (
		{
			u.name: u
			for u in frappe.db.get_all(
				"User", filters={"name": ["in", user_ids]}, fields=["name", "full_name", "user_image", "username"]
			)
		}
		if user_ids
		else {}
	)

	for r in rows:
		u = users_by_id.get(r.user)
		r.full_name = u.full_name if u else None
		r.user_image = u.user_image if u else None
		r.username = u.username if u else None

	for p in pending_invites:
		u = users_by_id.get(p.invited_user)
		p.full_name = u.full_name if u else None
		p.user_image = u.user_image if u else None

	return {
		# Admins are shown grouped in with editors ("Editors" section in the
		# UI), just badged distinctly — mirrors how the Frappe blog itself
		# groups them.
		"editors": [r for r in rows if r.role in ("Admin", "Editor")],
		"members": [r for r in rows if r.role == "Member"],
		"pending_invites": pending_invites,
		"my_role": _publication_role(publication),
	}


def _invite_to_publication(publication, user, role="Member"):
	"""Mirrors chat.py's _invite_to_group: adding someone is a request, not
	immediate membership — skip silently if they're already in, or already
	have a pending invite, rather than erroring on what's really a no-op."""
	if frappe.db.exists("Publication Member", {"publication": publication, "user": user}):
		return
	if frappe.db.exists(
		"Publication Invite", {"publication": publication, "invited_user": user, "status": "Pending"}
	):
		return
	invite = frappe.get_doc(
		{"doctype": "Publication Invite", "publication": publication, "invited_user": user, "role": role}
	)
	invite.insert(ignore_permissions=True)

	from my_new_app.follow import _notify

	title = frappe.db.get_value("Publication", publication, "title") or "a publication"
	_notify(
		recipient=user,
		actor=frappe.session.user,
		notif_type="Publication Invite",
		message=f'invited you to join "{title}" as {"an" if role == "Editor" else "a"} {role.lower()}',
		reference_doctype="Publication Invite",
		reference_name=invite.name,
	)


@frappe.whitelist()
def invite_to_publication(publication, user, role="Member"):
	_require_publication_admin(publication)
	if role not in ("Editor", "Member"):
		frappe.throw("Invalid role")
	if user == frappe.session.user:
		frappe.throw("You're already in this publication")
	_invite_to_publication(publication, user, role)
	return "success"


@frappe.whitelist()
def cancel_publication_invite(name):
	invite = frappe.get_doc("Publication Invite", name)
	_require_publication_admin(invite.publication)
	frappe.delete_doc("Publication Invite", name, ignore_permissions=True)
	return "success"


@frappe.whitelist()
def respond_to_publication_invite(name, accept):
	invite = frappe.get_doc("Publication Invite", name)
	if invite.invited_user != frappe.session.user:
		frappe.throw("Not permitted", frappe.PermissionError)
	if invite.status != "Pending":
		return {"status": invite.status}

	accept = int(accept)
	invite.status = "Accepted" if accept else "Declined"
	invite.flags.ignore_permissions = True
	invite.save()

	if accept:
		if not frappe.db.exists(
			"Publication Member", {"publication": invite.publication, "user": frappe.session.user}
		):
			member = frappe.get_doc(
				{
					"doctype": "Publication Member",
					"publication": invite.publication,
					"user": frappe.session.user,
					"role": invite.role,
				}
			)
			member.insert(ignore_permissions=True)

		from my_new_app.follow import _notify

		title = frappe.db.get_value("Publication", invite.publication, "title") or "the publication"
		_notify(
			recipient=invite.invited_by,
			actor=frappe.session.user,
			notif_type="Publication Invite",
			message=f'joined "{title}"',
			reference_doctype="Publication",
			reference_name=invite.publication,
		)

	return {"status": invite.status, "publication": invite.publication if accept else None}


@frappe.whitelist()
def remove_publication_member(publication, user):
	_require_publication_admin(publication)
	if user == frappe.session.user:
		frappe.throw('Use "Leave" to remove yourself')
	name = frappe.db.get_value("Publication Member", {"publication": publication, "user": user})
	if not name:
		frappe.throw("That person isn't in this publication")
	frappe.delete_doc("Publication Member", name, ignore_permissions=True)
	return "success"


@frappe.whitelist()
def set_publication_member_role(publication, user, role):
	_require_publication_admin(publication)
	if role not in ("Admin", "Editor", "Member"):
		frappe.throw("Invalid role")

	name = frappe.db.get_value("Publication Member", {"publication": publication, "user": user})
	if not name:
		frappe.throw("That person isn't in this publication")

	if role != "Admin":
		current_role = frappe.db.get_value("Publication Member", name, "role")
		if current_role == "Admin":
			admin_count = frappe.db.count("Publication Member", {"publication": publication, "role": "Admin"})
			if admin_count <= 1:
				frappe.throw("A publication needs at least one admin")

	frappe.db.set_value("Publication Member", name, "role", role)
	return "success"


@frappe.whitelist()
def get_post(post_id):
	post = frappe.get_doc("Post", post_id)
	post.check_permission("read")
	post = post.as_dict()

	post.like_count = frappe.db.count("Like", {"reference_type": "Post", "reference_name": post_id})
	post.comment_count = frappe.db.count("Post Comment", {"post": post_id})
	post.liked_by_me = bool(
		frappe.session.user != "Guest"
		and frappe.db.exists(
			"Like",
			{"reference_type": "Post", "reference_name": post_id, "user": frappe.session.user},
		)
	)
	post.tags = [t.strip() for t in (post.tags or "").split(",") if t.strip()]
	# Older Image posts predate the Images table and only have the single
	# legacy `attachment` field — surface it the same way so the frontend
	# only ever deals with a list.
	if post.post_type == "Image" and not post.images and post.attachment:
		post.images = [{"image": post.attachment}]
	post.author_bio = frappe.db.get_value("User", post.author, "bio")
	post.author_follower_count = _subscriber_count("User", post.author)
	post.author_is_private = frappe.db.get_value("User", post.author, "is_private")

	from my_new_app.follow import get_follow_state

	follow_state = (
		get_follow_state(post.author) if frappe.session.user != "Guest" else {"following": False, "pending": False}
	)
	post.author_following_by_me = follow_state["following"]
	post.author_follow_pending = follow_state["pending"]
	post.saved_by_me = bool(
		frappe.session.user != "Guest"
		and frappe.db.exists("Saved Post", {"post": post_id, "user": frappe.session.user})
	)

	return post


def _check_post_visible(post_id):
	row = frappe.db.get_value("Post", post_id, ["status", "author"], as_dict=True)
	if not row:
		frappe.throw("Post not found", frappe.DoesNotExistError)
	if row.status != "Published" and row.author != frappe.session.user:
		frappe.throw("Not permitted", frappe.PermissionError)


@frappe.whitelist()
def toggle_like(reference_type, reference_name):
	user = frappe.session.user
	if user == "Guest":
		frappe.throw("Not permitted", frappe.PermissionError)
	if reference_type == "Post":
		_check_post_visible(reference_name)

	existing = frappe.db.exists(
		"Like", {"reference_type": reference_type, "reference_name": reference_name, "user": user}
	)
	if existing:
		frappe.delete_doc("Like", existing, ignore_permissions=True)
		liked = False
	else:
		like = frappe.get_doc(
			{
				"doctype": "Like",
				"reference_type": reference_type,
				"reference_name": reference_name,
			}
		)
		like.flags.ignore_permissions = True
		like.insert()
		liked = True

		if reference_type == "Post":
			from my_new_app.follow import _notify

			post_author = frappe.db.get_value("Post", reference_name, "author")
			_notify(post_author, user, "Like", "liked your post", "Post", reference_name)
		elif reference_type == "Post Comment":
			from my_new_app.follow import _notify

			comment_author = frappe.db.get_value("Post Comment", reference_name, "comment_by")
			_notify(comment_author, user, "Like", "liked your comment", "Post Comment", reference_name)

	count = frappe.db.count("Like", {"reference_type": reference_type, "reference_name": reference_name})
	return {"liked": liked, "count": count}


@frappe.whitelist()
def list_comments(post):
	_check_post_visible(post)
	rows = frappe.db.get_all(
		"Post Comment",
		filters={"post": post},
		fields=[
			"name",
			"parent_comment",
			"comment_by",
			"comment_by_name",
			"comment_by_image",
			"content",
			"creation",
		],
		order_by="creation desc",
	)

	liked_names = set()
	if rows and frappe.session.user != "Guest":
		liked_names = set(
			frappe.db.get_all(
				"Like",
				filters={
					"reference_type": "Post Comment",
					"reference_name": ["in", [r.name for r in rows]],
					"user": frappe.session.user,
				},
				pluck="reference_name",
			)
		)

	like_counts = {}
	if rows:
		for reference_name in frappe.db.get_all(
			"Like",
			filters={"reference_type": "Post Comment", "reference_name": ["in", [r.name for r in rows]]},
			pluck="reference_name",
		):
			like_counts[reference_name] = like_counts.get(reference_name, 0) + 1

	for row in rows:
		row.like_count = like_counts.get(row.name, 0)
		row.liked_by_me = row.name in liked_names
	return rows


@frappe.whitelist()
def delete_comment(name):
	comment = frappe.get_doc("Post Comment", name)
	if comment.comment_by != frappe.session.user:
		frappe.throw("You can only delete your own comments", frappe.PermissionError)

	# Threading is one level deep (see add_comment) — deleting a top-level
	# comment takes its replies with it rather than leaving them orphaned.
	if not comment.parent_comment:
		frappe.db.delete("Post Comment", {"parent_comment": name})
	frappe.delete_doc("Post Comment", name, ignore_permissions=True)
	return "success"


@frappe.whitelist()
def add_comment(post, content, parent_comment=None):
	_check_post_visible(post)

	if parent_comment:
		parent = frappe.db.get_value(
			"Post Comment", parent_comment, ["post", "parent_comment", "comment_by"], as_dict=True
		)
		if not parent or parent.post != post:
			frappe.throw("Comment not found", frappe.DoesNotExistError)
		# Keep threading a single level deep: replying to a reply attaches to
		# its top-level ancestor instead of nesting further.
		parent_comment = parent.parent_comment or parent_comment

	comment = frappe.get_doc(
		{"doctype": "Post Comment", "post": post, "content": content, "parent_comment": parent_comment}
	)
	comment.insert()

	from my_new_app.follow import _notify

	if parent_comment:
		reply_to = frappe.db.get_value("Post Comment", parent_comment, "comment_by")
		if reply_to != frappe.session.user:
			_notify(reply_to, frappe.session.user, "Comment", "replied to your comment", "Post Comment", parent_comment)
	else:
		post_author = frappe.db.get_value("Post", post, "author")
		_notify(post_author, frappe.session.user, "Comment", "commented on your post", "Post", post)

	return comment.as_dict()


@frappe.whitelist()
def update_profile(
	full_name=None,
	bio=None,
	headline=None,
	user_image=None,
	location=None,
	job_title=None,
	company=None,
	is_private=None,
):
	user = frappe.session.user
	if user == "Guest":
		frappe.throw("Not permitted", frappe.PermissionError)

	doc = frappe.get_doc("User", user)
	if full_name is not None:
		# User.validate() recomputes full_name from first_name/last_name on every
		# save (set_full_name()), so assigning full_name directly here would be
		# silently overwritten — split it into the fields that actually stick.
		parts = full_name.strip().split(" ", 1)
		doc.first_name = parts[0]
		doc.last_name = parts[1] if len(parts) > 1 else ""
	if bio is not None:
		doc.bio = bio
	if headline is not None:
		doc.headline = headline
	if user_image is not None:
		doc.user_image = user_image
	if location is not None:
		doc.location = location
	if job_title is not None:
		doc.job_title = job_title
	if company is not None:
		doc.company = company
	if is_private is not None:
		doc.is_private = int(is_private)

	doc.flags.ignore_permissions = True
	doc.save()
	return "success"


@frappe.whitelist()
def add_education(school, degree=None, field_of_study=None, start_year=None, end_year=None):
	entry = frappe.get_doc(
		{
			"doctype": "Education Entry",
			"school": school,
			"degree": degree,
			"field_of_study": field_of_study,
			"start_year": start_year,
			"end_year": end_year,
		}
	)
	entry.insert()
	return entry.as_dict()


@frappe.whitelist()
def update_education(name, school=None, degree=None, field_of_study=None, start_year=None, end_year=None):
	doc = frappe.get_doc("Education Entry", name)
	if school is not None:
		doc.school = school
	if degree is not None:
		doc.degree = degree
	if field_of_study is not None:
		doc.field_of_study = field_of_study
	if start_year is not None:
		doc.start_year = start_year
	if end_year is not None:
		doc.end_year = end_year
	doc.save()
	return doc.as_dict()


@frappe.whitelist()
def delete_education(name):
	frappe.delete_doc("Education Entry", name)
	return "success"


@frappe.whitelist()
def add_work(company, title=None, start_date=None, end_date=None, description=None):
	entry = frappe.get_doc(
		{
			"doctype": "Work Entry",
			"company": company,
			"title": title,
			"start_date": start_date,
			"end_date": end_date,
			"description": description,
		}
	)
	entry.insert()
	return entry.as_dict()


@frappe.whitelist()
def update_work(name, company=None, title=None, start_date=None, end_date=None, description=None):
	doc = frappe.get_doc("Work Entry", name)
	if company is not None:
		doc.company = company
	if title is not None:
		doc.title = title
	if start_date is not None:
		doc.start_date = start_date
	if end_date is not None:
		doc.end_date = end_date
	if description is not None:
		doc.description = description
	doc.save()
	return doc.as_dict()


@frappe.whitelist()
def delete_work(name):
	frappe.delete_doc("Work Entry", name)
	return "success"


@frappe.whitelist()
def toggle_save_post(post):
	user = frappe.session.user
	if user == "Guest":
		frappe.throw("Not permitted", frappe.PermissionError)
	_check_post_visible(post)

	existing = frappe.db.exists("Saved Post", {"post": post, "user": user})
	if existing:
		frappe.delete_doc("Saved Post", existing, ignore_permissions=True)
		return {"saved": False}

	doc = frappe.get_doc({"doctype": "Saved Post", "post": post})
	doc.flags.ignore_permissions = True
	doc.insert()
	return {"saved": True}


@frappe.whitelist()
def list_saved_posts():
	rows = frappe.db.get_all(
		"Saved Post",
		filters={"user": frappe.session.user},
		fields=["name", "post", "creation"],
		order_by="creation desc",
	)
	if not rows:
		return []

	posts_by_name = {
		p.name: p
		for p in frappe.db.get_all(
			"Post",
			filters={"name": ["in", [r.post for r in rows]]},
			fields=[
				"name",
				"title",
				"display_title",
				"content",
				"post_type",
				"attachment",
				"cover_image",
				"author_name",
				"author_image",
				"status",
			],
		)
	}

	result = []
	for row in rows:
		post = posts_by_name.get(row.post)
		if not post or post.status != "Published":
			continue
		post.saved_name = row.name
		post.saved_at = row.creation
		result.append(post)
	return result


@frappe.whitelist()
def list_categories():
	return frappe.db.get_all("Category", fields=["name", "title"], order_by="title asc")


@frappe.whitelist()
def create_category(title):
	title = (title or "").strip()
	if not title:
		frappe.throw("Category name is required")
	if frappe.db.exists("Category", title):
		frappe.throw("That category already exists")

	doc = frappe.get_doc({"doctype": "Category", "title": title})
	doc.insert(ignore_permissions=True)
	return {"name": doc.name, "title": doc.title}


@frappe.whitelist()
def delete_category(name):
	frappe.delete_doc("Category", name)
	return "success"
