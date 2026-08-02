import { useCall } from 'frappe-ui'

export const unreadNotifCount = useCall({
  url: '/api/v2/method/my_new_app.follow.unread_notification_count',
})
