import frappe


def _notify(recipient, actor, notif_type, message, reference_doctype=None, reference_name=None):
	if not recipient or recipient == actor:
		return

	actor_name, actor_image = None, None
	if actor:
		actor_name, actor_image = frappe.db.get_value("User", actor, ["full_name", "user_image"])

	doc = frappe.get_doc(
		{
			"doctype": "App Notification",
			"recipient": recipient,
			"actor": actor,
			"actor_name": actor_name,
			"actor_image": actor_image,
			"type": notif_type,
			"reference_doctype": reference_doctype,
			"reference_name": reference_name,
			"message": message,
		}
	)
	doc.flags.ignore_permissions = True
	doc.insert()
	frappe.publish_realtime("notification:new", doc.as_dict(), user=recipient, after_commit=True)


def notify_followers_of_new_post(post):
	followers = frappe.db.get_all(
		"Subscription", filters={"reference_type": "User", "reference_name": post.author}, fields=["subscriber"]
	)
	title = post.title or "a new post"
	for f in followers:
		_notify(
			f.subscriber,
			post.author,
			"New Post",
			f"published {title}",
			"Post",
			post.name,
		)


@frappe.whitelist()
def get_follow_state(user):
	me = frappe.session.user
	following = bool(
		frappe.db.exists("Subscription", {"reference_type": "User", "reference_name": user, "subscriber": me})
	)
	pending = bool(
		frappe.db.exists("Follow Request", {"from_user": me, "to_user": user, "status": "Pending"})
	)
	return {"following": following, "pending": pending}


@frappe.whitelist()
def follow_user(user):
	me = frappe.session.user
	if user == me:
		frappe.throw("You can't follow yourself")

	if frappe.db.exists("Subscription", {"reference_type": "User", "reference_name": user, "subscriber": me}):
		return {"status": "following"}

	is_private = frappe.db.get_value("User", user, "is_private")
	if is_private:
		if frappe.db.exists("Follow Request", {"from_user": me, "to_user": user, "status": "Pending"}):
			return {"status": "requested"}
		req = frappe.get_doc({"doctype": "Follow Request", "to_user": user})
		req.insert(ignore_permissions=True)
		_notify(user, me, "Follow Request", "requested to follow you", "Follow Request", req.name)
		return {"status": "requested"}

	sub = frappe.get_doc({"doctype": "Subscription", "reference_type": "User", "reference_name": user})
	sub.flags.ignore_permissions = True
	sub.insert()
	_notify(user, me, "New Follower", "started following you", "User", me)
	return {"status": "following"}


@frappe.whitelist()
def unfollow_user(user):
	me = frappe.session.user
	frappe.db.delete("Subscription", {"reference_type": "User", "reference_name": user, "subscriber": me})
	frappe.db.delete("Follow Request", {"from_user": me, "to_user": user, "status": "Pending"})
	return {"status": "not_following"}


@frappe.whitelist()
def list_follow_requests():
	rows = frappe.db.get_all(
		"Follow Request",
		filters={"to_user": frappe.session.user, "status": "Pending"},
		fields=["name", "from_user", "creation"],
		order_by="creation desc",
	)
	for r in rows:
		r.from_user_name = frappe.db.get_value("User", r.from_user, "full_name")
		r.from_user_image = frappe.db.get_value("User", r.from_user, "user_image")
	return rows


@frappe.whitelist()
def respond_to_follow_request(name, accept):
	req = frappe.get_doc("Follow Request", name)
	if req.to_user != frappe.session.user:
		frappe.throw("Not permitted", frappe.PermissionError)

	accept = int(accept)
	req.status = "Accepted" if accept else "Declined"
	req.flags.ignore_permissions = True
	req.save()

	if accept:
		if not frappe.db.exists(
			"Subscription",
			{"reference_type": "User", "reference_name": frappe.session.user, "subscriber": req.from_user},
		):
			sub = frappe.get_doc(
				{
					"doctype": "Subscription",
					"reference_type": "User",
					"reference_name": frappe.session.user,
					"subscriber": req.from_user,
				}
			)
			sub.flags.ignore_permissions = True
			sub.insert()
		_notify(
			req.from_user,
			frappe.session.user,
			"Follow Accepted",
			"accepted your follow request",
			"User",
			frappe.session.user,
		)

	return {"status": req.status}


@frappe.whitelist()
def list_notifications():
	rows = frappe.db.get_all(
		"App Notification",
		filters={"recipient": frappe.session.user},
		fields=[
			"name",
			"actor",
			"actor_name",
			"actor_image",
			"type",
			"reference_doctype",
			"reference_name",
			"message",
			"is_read",
			"creation",
		],
		order_by="creation desc",
		limit_page_length=50,
	)
	for r in rows:
		if r.type == "Follow Request" and r.reference_doctype == "Follow Request":
			r.request_status = frappe.db.get_value("Follow Request", r.reference_name, "status")
		elif r.type == "Group Invite" and r.reference_doctype == "Group Invite":
			r.request_status = frappe.db.get_value("Group Invite", r.reference_name, "status")
		elif r.type == "Publication Invite" and r.reference_doctype == "Publication Invite":
			r.request_status = frappe.db.get_value("Publication Invite", r.reference_name, "status")
	return rows


@frappe.whitelist()
def unread_notification_count():
	return frappe.db.count("App Notification", {"recipient": frappe.session.user, "is_read": 0})


@frappe.whitelist()
def mark_notification_read(name=None):
	if name:
		frappe.db.set_value("App Notification", name, "is_read", 1)
	else:
		frappe.db.set_value("App Notification", {"recipient": frappe.session.user, "is_read": 0}, "is_read", 1)
	return "success"
