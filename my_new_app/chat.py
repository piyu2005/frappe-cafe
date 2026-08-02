import re
import urllib.request

import frappe
from frappe.utils import now_datetime

URL_RE = re.compile(r"(https?://[^\s]+)")


def _is_member(conversation, user=None):
	user = user or frappe.session.user
	return frappe.db.exists("Conversation Member", {"conversation": conversation, "user": user})


def _require_member(conversation):
	if not _is_member(conversation):
		frappe.throw("Not permitted", frappe.PermissionError)


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
				"last_message": last_message.content if last_message else None,
				"last_message_at": last_message.creation if last_message else None,
				"unread_count": 0 if m.muted else unread_count,
			}
		)

	result.sort(key=lambda r: r["last_message_at"] or "", reverse=True)
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
	for row in rows:
		row.reactions = _group_reactions(row.name)
	return rows


@frappe.whitelist()
def send_message(conversation, content=None, attachment=None):
	_require_member(conversation)
	if not content and not attachment:
		frappe.throw("Message cannot be empty")

	others = _other_members(conversation)
	if len(others) == 1 and _is_blocked(frappe.session.user, others[0]):
		frappe.throw("You can't message this user")

	doc = frappe.get_doc(
		{"doctype": "Message", "conversation": conversation, "content": content, "attachment": attachment}
	)

	if content:
		match = URL_RE.search(content)
		if match:
			doc.update(_unfurl(match.group(1)))

	doc.insert(ignore_permissions=True)

	payload = doc.as_dict()
	payload["reactions"] = []
	for other in others:
		frappe.publish_realtime("chat:new_message", payload, user=other, after_commit=True)

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
		"User", filters=filters, fields=["name", "full_name", "user_image"], order_by="full_name asc", limit_page_length=20
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
	return frappe.db.get_all(
		"Message",
		filters={"conversation": conversation, "content": ["like", f"%{query}%"]},
		fields=["name", "content", "sender_name", "creation"],
		order_by="creation desc",
		limit_page_length=50,
	)
