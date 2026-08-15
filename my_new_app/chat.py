import re
import urllib.request

import frappe
from frappe.utils import now_datetime

from my_new_app.api import _check_post_visible
from my_new_app.follow import _notify

URL_RE = re.compile(r"(https?://[^\s]+)")
HTML_TAG_RE = re.compile(r"<[^>]*>")
# Mentions render as `<span class="mention" data-type="mention" data-id="...">`
# (frappe-ui's Mention node) — attribute order isn't guaranteed, so match the
# whole opening tag first, then pull data-id out of that.
MENTION_SPAN_RE = re.compile(r'<span[^>]*class="mention"[^>]*>', re.I)
DATA_ID_RE = re.compile(r'data-id="([^"]*)"')


def _extract_mentions(content):
	if not content:
		return []
	ids = []
	for span in MENTION_SPAN_RE.findall(content):
		match = DATA_ID_RE.search(span)
		if match and match.group(1):
			ids.append(match.group(1))
	return ids


def _preview_text(content):
	"""Plain-text preview for conversation/search listings — messages composed
	with the rich-text composer store HTML, which shouldn't leak into a
	one-line snippet."""
	if not content:
		return content
	stripped = HTML_TAG_RE.sub(" ", content)
	return re.sub(r"\s+", " ", stripped).strip() or None


def _is_member(conversation, user=None):
	user = user or frappe.session.user
	return frappe.db.exists("Conversation Member", {"conversation": conversation, "user": user})


def _require_member(conversation):
	if not _is_member(conversation):
		frappe.throw("Not permitted", frappe.PermissionError)


def _is_admin(conversation, user=None):
	user = user or frappe.session.user
	return bool(
		frappe.db.get_value("Conversation Member", {"conversation": conversation, "user": user}, "is_admin")
	)


def _require_admin(conversation):
	_require_member(conversation)
	if not _is_admin(conversation):
		frappe.throw("Only group admins can do this", frappe.PermissionError)


def _is_blocked(user_a, user_b):
	return bool(
		frappe.db.exists("Blocked User", {"blocker": user_a, "blocked": user_b})
		or frappe.db.exists("Blocked User", {"blocker": user_b, "blocked": user_a})
	)


def _other_members(conversation, exclude=None):
	exclude = exclude or frappe.session.user
	rows = frappe.db.get_all("Conversation Member", filters={"conversation": conversation}, fields=["user"])
	return [r.user for r in rows if r.user != exclude]


def _group_reactions(message):
	reactions = frappe.db.get_all("Message Reaction", filters={"message": message}, fields=["emoji", "user"])
	grouped = {}
	for r in reactions:
		grouped.setdefault(r.emoji, []).append(r.user)
	return [
		{"emoji": emoji, "count": len(users), "reacted_by_me": frappe.session.user in users}
		for emoji, users in grouped.items()
	]


def _unfurl(url):
	try:
		req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
		with urllib.request.urlopen(req, timeout=3) as resp:
			html = resp.read(200000).decode("utf-8", errors="ignore")

		def meta(prop):
			m = re.search(
				rf'<meta[^>]+property=["\']og:{prop}["\'][^>]+content=["\']([^"\']+)["\']', html, re.I
			)
			if not m:
				m = re.search(
					rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:{prop}["\']', html, re.I
				)
			return m.group(1) if m else None

		title = meta("title")
		if not title:
			m = re.search(r"<title[^>]*>([^<]+)</title>", html, re.I)
			title = m.group(1).strip() if m else url

		return {
			"link_url": url,
			"link_title": title,
			"link_description": meta("description"),
			"link_image": meta("image"),
		}
	except Exception:
		return {"link_url": url, "link_title": url, "link_description": None, "link_image": None}


def _post_card(post_id):
	post = frappe.db.get_value(
		"Post",
		post_id,
		["title", "post_type", "cover_image", "attachment", "author_name"],
		as_dict=True,
	)
	image = post.cover_image or (post.attachment if post.post_type != "Video" else None)
	return {
		"shared_post": post_id,
		"link_url": f"/posts/{post_id}",
		"link_title": post.title,
		"link_description": f"by {post.author_name}" if post.author_name else None,
		"link_image": image,
	}


def _poll_payload(poll_name):
	poll = frappe.db.get_value(
		"Poll", poll_name, ["question", "allow_multiple", "anonymous", "close_at"], as_dict=True
	)
	if not poll:
		return None

	options = frappe.db.get_all(
		"Poll Option", filters={"poll": poll_name}, fields=["name", "option_text"], order_by="creation asc"
	)
	votes = frappe.db.get_all("Poll Vote", filters={"poll": poll_name}, fields=["poll_option", "user"])

	counts = {}
	my_votes = set()
	for v in votes:
		counts[v.poll_option] = counts.get(v.poll_option, 0) + 1
		if v.user == frappe.session.user:
			my_votes.add(v.poll_option)

	for o in options:
		o.vote_count = counts.get(o.name, 0)
		o.voted_by_me = o.name in my_votes

	is_closed = bool(poll.close_at and now_datetime() > frappe.utils.get_datetime(poll.close_at))

	return {
		"name": poll_name,
		"question": poll.question,
		"allow_multiple": poll.allow_multiple,
		"anonymous": poll.anonymous,
		"close_at": poll.close_at,
		"is_closed": is_closed,
		"total_votes": len(votes),
		"options": options,
	}


@frappe.whitelist()
def create_poll(conversation, question, options, allow_multiple=0, anonymous=0, close_at=None):
	_require_member(conversation)
	if isinstance(options, str):
		options = frappe.parse_json(options)
	options = [o.strip() for o in (options or []) if o and o.strip()]

	if not question or not question.strip():
		frappe.throw("Poll question is required")
	if len(options) < 2:
		frappe.throw("Add at least 2 options")

	others = _other_members(conversation)
	if len(others) == 1 and _is_blocked(frappe.session.user, others[0]):
		frappe.throw("You can't message this user")

	poll = frappe.get_doc(
		{
			"doctype": "Poll",
			"question": question.strip(),
			"allow_multiple": 1 if int(allow_multiple or 0) else 0,
			"anonymous": 1 if int(anonymous or 0) else 0,
			"close_at": close_at or None,
		}
	)
	poll.insert(ignore_permissions=True)

	for text in options:
		option = frappe.get_doc({"doctype": "Poll Option", "poll": poll.name, "option_text": text})
		option.insert(ignore_permissions=True)

	doc = frappe.get_doc({"doctype": "Message", "conversation": conversation, "poll": poll.name})
	doc.insert(ignore_permissions=True)

	payload = doc.as_dict()
	payload["reactions"] = []
	payload["attachments"] = []
	payload["poll_data"] = _poll_payload(poll.name)
	for other in others:
		frappe.publish_realtime("chat:new_message", payload, user=other, after_commit=True)

	return payload


@frappe.whitelist()
def toggle_poll_vote(option):
	poll_option = frappe.db.get_value("Poll Option", option, ["poll"], as_dict=True)
	if not poll_option:
		frappe.throw("Option not found", frappe.DoesNotExistError)

	poll = frappe.db.get_value("Poll", poll_option.poll, ["allow_multiple", "close_at"], as_dict=True)
	message = frappe.db.get_value("Message", {"poll": poll_option.poll}, ["name", "conversation"], as_dict=True)
	if not message:
		frappe.throw("Not permitted", frappe.PermissionError)
	_require_member(message.conversation)

	if poll.close_at and now_datetime() > frappe.utils.get_datetime(poll.close_at):
		frappe.throw("This poll is closed")

	user = frappe.session.user
	existing = frappe.db.exists("Poll Vote", {"poll_option": option, "user": user})
	if existing:
		frappe.delete_doc("Poll Vote", existing, ignore_permissions=True)
	else:
		if not poll.allow_multiple:
			for other_vote in frappe.db.get_all(
				"Poll Vote", filters={"poll": poll_option.poll, "user": user}, pluck="name"
			):
				frappe.delete_doc("Poll Vote", other_vote, ignore_permissions=True)
		vote = frappe.get_doc({"doctype": "Poll Vote", "poll": poll_option.poll, "poll_option": option})
		vote.insert(ignore_permissions=True)

	result = _poll_payload(poll_option.poll)
	for other in _other_members(message.conversation):
		frappe.publish_realtime(
			"chat:poll_update", {"message": message.name, "poll_data": result}, user=other, after_commit=True
		)
	return result


@frappe.whitelist()
def list_conversations():
	user = frappe.session.user
	memberships = frappe.db.get_all(
		"Conversation Member", filters={"user": user}, fields=["conversation", "muted", "last_read"]
	)

	result = []
	for m in memberships:
		conv = frappe.db.get_value("Conversation", m.conversation, ["is_group", "title"], as_dict=True)
		others = _other_members(m.conversation, exclude=user)

		if conv.is_group:
			display_name = conv.title or "Group"
			display_image = None
			other_user = None
		else:
			other_user = others[0] if others else None
			display_name = frappe.db.get_value("User", other_user, "full_name") if other_user else "Unknown"
			display_image = frappe.db.get_value("User", other_user, "user_image") if other_user else None

		last_message = frappe.db.get_value(
			"Message",
			{"conversation": m.conversation},
			["content", "creation", "sender"],
			order_by="creation desc",
			as_dict=True,
		)
		unread_count = frappe.db.count(
			"Message",
			{
				"conversation": m.conversation,
				"sender": ["!=", user],
				"creation": [">", m.last_read or "1900-01-01"],
			},
		)

		result.append(
			{
				"conversation": m.conversation,
				"display_name": display_name,
				"display_image": display_image,
				"other_user": other_user,
				"is_group": conv.is_group,
				"muted": m.muted,
				"last_message": _preview_text(last_message.content) if last_message else None,
				"last_message_at": last_message.creation if last_message else None,
				"unread_count": 0 if m.muted else unread_count,
			}
		)

	# last_message_at is a real datetime for conversations that have a
	# message, or None for one that doesn't yet (a freshly created group,
	# most commonly) — sort keys need to be one consistent type, so stringify
	# rather than mixing datetime and "" (which Python 3 refuses to compare).
	result.sort(key=lambda r: str(r["last_message_at"] or ""), reverse=True)
	return result


@frappe.whitelist()
def unread_message_count():
	memberships = frappe.db.get_all(
		"Conversation Member", filters={"user": frappe.session.user, "muted": 0}, fields=["conversation", "last_read"]
	)
	total = 0
	for m in memberships:
		total += frappe.db.count(
			"Message",
			{
				"conversation": m.conversation,
				"sender": ["!=", frappe.session.user],
				"creation": [">", m.last_read or "1900-01-01"],
			},
		)
	return total


@frappe.whitelist()
def start_dm(other_user):
	user = frappe.session.user
	if other_user == user:
		frappe.throw("You can't message yourself")
	if _is_blocked(user, other_user):
		frappe.throw("You can't message this user")

	my_convs = frappe.db.get_all("Conversation Member", filters={"user": user}, fields=["conversation"])
	for c in my_convs:
		conv = frappe.db.get_value("Conversation", c.conversation, ["is_group"], as_dict=True)
		if conv and not conv.is_group:
			others = _other_members(c.conversation, exclude=user)
			if others == [other_user]:
				return {"conversation": c.conversation}

	conv = frappe.get_doc({"doctype": "Conversation", "is_group": 0})
	conv.insert(ignore_permissions=True)
	for u in (user, other_user):
		member = frappe.get_doc({"doctype": "Conversation Member", "conversation": conv.name, "user": u})
		member.insert(ignore_permissions=True)

	return {"conversation": conv.name}


@frappe.whitelist()
def get_conversation(conversation):
	_require_member(conversation)
	conv = frappe.db.get_value("Conversation", conversation, ["is_group", "title"], as_dict=True)
	others = _other_members(conversation)
	my_membership = frappe.db.get_value(
		"Conversation Member", {"conversation": conversation, "user": frappe.session.user}, ["muted"], as_dict=True
	)

	if conv.is_group:
		display_name = conv.title or "Group"
		display_image = None
		other_user = None
	else:
		other_user = others[0] if others else None
		display_name = frappe.db.get_value("User", other_user, "full_name") if other_user else "Unknown"
		display_image = frappe.db.get_value("User", other_user, "user_image") if other_user else None

	other_last_read = None
	if other_user:
		other_last_read = frappe.db.get_value(
			"Conversation Member", {"conversation": conversation, "user": other_user}, "last_read"
		)

	return {
		"conversation": conversation,
		"is_group": conv.is_group,
		"display_name": display_name,
		"display_image": display_image,
		"other_user": other_user,
		"is_blocked": _is_blocked(frappe.session.user, other_user) if other_user else False,
		"i_blocked_them": bool(
			other_user
			and frappe.db.exists("Blocked User", {"blocker": frappe.session.user, "blocked": other_user})
		),
		"muted": my_membership.muted if my_membership else False,
		"other_last_read": other_last_read,
	}


def _invite_to_group(conversation, user):
	"""Adding someone to a group is a request, not immediate membership —
	skip silently if they're already in, or already have a pending invite,
	rather than erroring on what's really a no-op from the caller's POV."""
	if frappe.db.exists("Conversation Member", {"conversation": conversation, "user": user}):
		return
	if frappe.db.exists(
		"Group Invite", {"conversation": conversation, "invited_user": user, "status": "Pending"}
	):
		return
	invite = frappe.get_doc(
		{"doctype": "Group Invite", "conversation": conversation, "invited_user": user}
	)
	invite.insert(ignore_permissions=True)
	title = frappe.db.get_value("Conversation", conversation, "title") or "a group"
	_notify(
		recipient=user,
		actor=frappe.session.user,
		notif_type="Group Invite",
		message=f'invited you to join "{title}"',
		reference_doctype="Group Invite",
		reference_name=invite.name,
	)


@frappe.whitelist()
def create_group(title, members):
	if isinstance(members, str):
		members = frappe.parse_json(members)
	# Dedupe while preserving order, and never invite yourself — you're added
	# as the (first, admin) member below regardless.
	members = list(dict.fromkeys(m for m in (members or []) if m and m != frappe.session.user))

	title = (title or "").strip()
	if not title:
		frappe.throw("Give the group a name")
	if not members:
		frappe.throw("Add at least one person to invite")

	conv = frappe.get_doc({"doctype": "Conversation", "is_group": 1, "title": title})
	conv.insert(ignore_permissions=True)

	creator = frappe.get_doc(
		{
			"doctype": "Conversation Member",
			"conversation": conv.name,
			"user": frappe.session.user,
			"is_admin": 1,
		}
	)
	creator.insert(ignore_permissions=True)

	for user in members:
		_invite_to_group(conv.name, user)

	return {"conversation": conv.name}


@frappe.whitelist()
def invite_to_group(conversation, user):
	_require_admin(conversation)
	if user == frappe.session.user:
		frappe.throw("You're already in this group")
	_invite_to_group(conversation, user)
	return "success"


@frappe.whitelist()
def cancel_group_invite(name):
	invite = frappe.get_doc("Group Invite", name)
	_require_admin(invite.conversation)
	frappe.delete_doc("Group Invite", name, ignore_permissions=True)
	return "success"


@frappe.whitelist()
def respond_to_group_invite(name, accept):
	invite = frappe.get_doc("Group Invite", name)
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
			"Conversation Member", {"conversation": invite.conversation, "user": frappe.session.user}
		):
			member = frappe.get_doc(
				{
					"doctype": "Conversation Member",
					"conversation": invite.conversation,
					"user": frappe.session.user,
				}
			)
			member.insert(ignore_permissions=True)
		title = frappe.db.get_value("Conversation", invite.conversation, "title") or "the group"
		_notify(
			recipient=invite.invited_by,
			actor=frappe.session.user,
			notif_type="Group Invite",
			message=f'joined "{title}"',
			reference_doctype="Conversation",
			reference_name=invite.conversation,
		)

	return {"status": invite.status, "conversation": invite.conversation if accept else None}


@frappe.whitelist()
def list_group_members(conversation):
	_require_member(conversation)
	members = frappe.db.get_all(
		"Conversation Member",
		filters={"conversation": conversation},
		fields=["name", "user", "is_admin", "creation"],
		order_by="creation asc",
	)
	for m in members:
		m.full_name = frappe.db.get_value("User", m.user, "full_name")
		m.user_image = frappe.db.get_value("User", m.user, "user_image")

	pending_invites = frappe.db.get_all(
		"Group Invite",
		filters={"conversation": conversation, "status": "Pending"},
		fields=["name", "invited_user", "creation"],
		order_by="creation desc",
	)
	for p in pending_invites:
		p.full_name = frappe.db.get_value("User", p.invited_user, "full_name")
		p.user_image = frappe.db.get_value("User", p.invited_user, "user_image")

	return {
		"members": members,
		"pending_invites": pending_invites,
		"my_is_admin": _is_admin(conversation),
	}


@frappe.whitelist()
def remove_group_member(conversation, user):
	_require_admin(conversation)
	if user == frappe.session.user:
		frappe.throw('Use "Leave group" to remove yourself')
	name = frappe.db.get_value("Conversation Member", {"conversation": conversation, "user": user})
	if not name:
		frappe.throw("That person isn't in this group")
	frappe.delete_doc("Conversation Member", name, ignore_permissions=True)
	return "success"


@frappe.whitelist()
def set_group_admin(conversation, user, is_admin):
	_require_admin(conversation)
	is_admin = int(is_admin)
	if not is_admin:
		admin_count = frappe.db.count("Conversation Member", {"conversation": conversation, "is_admin": 1})
		if admin_count <= 1:
			frappe.throw("A group needs at least one admin")
	name = frappe.db.get_value("Conversation Member", {"conversation": conversation, "user": user})
	if not name:
		frappe.throw("That person isn't in this group")
	frappe.db.set_value("Conversation Member", name, "is_admin", is_admin)
	return "success"


@frappe.whitelist()
def rename_group(conversation, title):
	_require_admin(conversation)
	title = (title or "").strip()
	if not title:
		frappe.throw("Give the group a name")
	frappe.db.set_value("Conversation", conversation, "title", title)
	return "success"


@frappe.whitelist()
def leave_group(conversation):
	_require_member(conversation)
	name = frappe.db.get_value(
		"Conversation Member", {"conversation": conversation, "user": frappe.session.user}
	)
	was_admin = _is_admin(conversation)
	frappe.delete_doc("Conversation Member", name, ignore_permissions=True)

	remaining = frappe.db.get_all(
		"Conversation Member",
		filters={"conversation": conversation},
		fields=["name", "is_admin"],
		order_by="creation asc",
	)
	if not remaining:
		# No one left — nothing more to leave, so clean up rather than leave a
		# dangling empty group around forever.
		frappe.delete_doc("Conversation", conversation, ignore_permissions=True, force=True)
	elif was_admin and not any(r.is_admin for r in remaining):
		# Never leave a group with zero admins — hand it to whoever's been in
		# it longest.
		frappe.db.set_value("Conversation Member", remaining[0].name, "is_admin", 1)

	return "success"


@frappe.whitelist()
def list_mentionable_users(conversation):
	"""Mention candidates for this conversation's composer — anyone on the
	platform, not just this conversation's members. `conversation` just
	confirms the caller is actually part of an active chat before handing
	back the list."""
	_require_member(conversation)
	return frappe.db.get_all(
		"User",
		filters={"enabled": 1, "user_type": "Website User", "name": ["not in", [frappe.session.user, "Guest"]]},
		fields=["name", "username", "full_name", "user_image"],
		order_by="full_name asc",
		limit_page_length=200,
	)


def _attachments_by_message(names):
	rows = frappe.db.get_all(
		"Message Attachment",
		filters={"parent": ["in", names]},
		fields=["parent", "file_url", "file_name", "file_size"],
		order_by="idx asc",
	)
	grouped = {}
	for r in rows:
		grouped.setdefault(r.parent, []).append(
			{"file_url": r.file_url, "file_name": r.file_name, "file_size": r.file_size}
		)
	return grouped


@frappe.whitelist()
def get_messages(conversation, start=0, limit=50):
	_require_member(conversation)
	rows = frappe.db.get_all(
		"Message",
		filters={"conversation": conversation},
		fields=[
			"name",
			"sender",
			"sender_name",
			"sender_image",
			"content",
			"attachment",
			"shared_post",
			"poll",
			"link_url",
			"link_title",
			"link_description",
			"link_image",
			"creation",
		],
		order_by="creation desc",
		start=int(start),
		page_length=int(limit),
	)
	rows.reverse()

	grouped = _attachments_by_message([r.name for r in rows])
	for row in rows:
		row.reactions = _group_reactions(row.name)
		# Older messages only have the single legacy `attachment` field;
		# surface it the same way so the frontend only ever deals with a list.
		row.attachments = grouped.get(row.name) or (
			[{"file_url": row.attachment, "file_name": row.attachment.rsplit("/", 1)[-1], "file_size": None}]
			if row.attachment
			else []
		)
		row.poll_data = _poll_payload(row.poll) if row.poll else None
	return rows


@frappe.whitelist()
def send_message(conversation, content=None, attachments=None, shared_post=None):
	_require_member(conversation)
	if isinstance(attachments, str):
		attachments = frappe.parse_json(attachments)
	attachments = attachments or []

	if not content and not attachments and not shared_post:
		frappe.throw("Message cannot be empty")

	others = _other_members(conversation)
	if len(others) == 1 and _is_blocked(frappe.session.user, others[0]):
		frappe.throw("You can't message this user")

	doc = frappe.get_doc({"doctype": "Message", "conversation": conversation, "content": content})
	for a in attachments:
		doc.append(
			"attachments",
			{"file_url": a.get("file_url"), "file_name": a.get("file_name"), "file_size": a.get("file_size")},
		)

	if shared_post:
		_check_post_visible(shared_post)
		doc.update(_post_card(shared_post))
	elif content:
		match = URL_RE.search(content)
		if match:
			doc.update(_unfurl(match.group(1)))

	doc.insert(ignore_permissions=True)

	payload = doc.as_dict()
	payload["reactions"] = []
	for other in others:
		frappe.publish_realtime("chat:new_message", payload, user=other, after_commit=True)

	# Mentions can name anyone, not just conversation members — but still
	# verify each id is a real, enabled user before notifying (never trust
	# "any id the client sent" on its own).
	mentioned_ids = set(_extract_mentions(content))
	if mentioned_ids:
		valid_mentions = frappe.db.get_all(
			"User", filters={"name": ["in", list(mentioned_ids)], "enabled": 1}, pluck="name"
		)
		others_set = set(others)
		for user in valid_mentions:
			# Only link back to the conversation if they can actually open it —
			# a mention of someone outside this chat still notifies them, but
			# routes to the mentioner's profile instead of a chat they can't see.
			is_member = user in others_set
			_notify(
				recipient=user,
				actor=frappe.session.user,
				notif_type="Mention",
				message="mentioned you in a message",
				reference_doctype="Conversation" if is_member else None,
				reference_name=conversation if is_member else None,
			)

	return payload


@frappe.whitelist()
def mark_read(conversation):
	_require_member(conversation)
	name = frappe.db.get_value(
		"Conversation Member", {"conversation": conversation, "user": frappe.session.user}
	)
	frappe.db.set_value("Conversation Member", name, "last_read", now_datetime())
	for other in _other_members(conversation):
		frappe.publish_realtime(
			"chat:read", {"conversation": conversation, "user": frappe.session.user}, user=other, after_commit=True
		)
	return "success"


@frappe.whitelist()
def set_typing(conversation):
	_require_member(conversation)
	for other in _other_members(conversation):
		frappe.publish_realtime(
			"chat:typing", {"conversation": conversation, "user": frappe.session.user}, user=other
		)
	return "success"


@frappe.whitelist()
def toggle_reaction(message, emoji):
	msg = frappe.db.get_value("Message", message, ["conversation"], as_dict=True)
	if not msg:
		frappe.throw("Message not found")
	_require_member(msg.conversation)

	existing = frappe.db.exists(
		"Message Reaction", {"message": message, "user": frappe.session.user, "emoji": emoji}
	)
	if existing:
		frappe.delete_doc("Message Reaction", existing, ignore_permissions=True)
	else:
		reaction = frappe.get_doc({"doctype": "Message Reaction", "message": message, "emoji": emoji})
		reaction.insert(ignore_permissions=True)

	result = _group_reactions(message)
	for other in _other_members(msg.conversation):
		frappe.publish_realtime(
			"chat:reaction", {"message": message, "reactions": result}, user=other, after_commit=True
		)
	return result


@frappe.whitelist()
def mute_conversation(conversation, muted):
	_require_member(conversation)
	name = frappe.db.get_value(
		"Conversation Member", {"conversation": conversation, "user": frappe.session.user}
	)
	frappe.db.set_value("Conversation Member", name, "muted", int(muted))
	return "success"


@frappe.whitelist()
def block_user(user):
	if not frappe.db.exists("Blocked User", {"blocker": frappe.session.user, "blocked": user}):
		doc = frappe.get_doc({"doctype": "Blocked User", "blocked": user})
		doc.insert(ignore_permissions=True)
	return "success"


@frappe.whitelist()
def unblock_user(user):
	frappe.db.delete("Blocked User", {"blocker": frappe.session.user, "blocked": user})
	frappe.db.commit()
	return "success"


@frappe.whitelist()
def list_blocked_users():
	rows = frappe.db.get_all(
		"Blocked User", filters={"blocker": frappe.session.user}, fields=["name", "blocked"]
	)
	for r in rows:
		r.full_name = frappe.db.get_value("User", r.blocked, "full_name")
		r.user_image = frappe.db.get_value("User", r.blocked, "user_image")
	return rows


@frappe.whitelist()
def search_people_to_message(query=None):
	filters = {"enabled": 1, "user_type": "Website User", "name": ["not in", [frappe.session.user, "Guest"]]}
	if query:
		filters["full_name"] = ["like", f"%{query}%"]

	people = frappe.db.get_all(
		"User",
		filters=filters,
		fields=["name", "full_name", "user_image", "username"],
		order_by="full_name asc",
		limit_page_length=20,
	)
	blocked_by_me = {
		b.blocked for b in frappe.db.get_all("Blocked User", filters={"blocker": frappe.session.user}, fields=["blocked"])
	}
	blocked_me = {
		b.blocker for b in frappe.db.get_all("Blocked User", filters={"blocked": frappe.session.user}, fields=["blocker"])
	}
	excluded = blocked_by_me | blocked_me
	return [p for p in people if p.name not in excluded]


@frappe.whitelist()
def search_messages(conversation, query):
	_require_member(conversation)
	rows = frappe.db.get_all(
		"Message",
		filters={"conversation": conversation, "content": ["like", f"%{query}%"]},
		fields=["name", "content", "sender_name", "creation"],
		order_by="creation desc",
		limit_page_length=50,
	)
	for row in rows:
		row.content = _preview_text(row.content)
	return rows
