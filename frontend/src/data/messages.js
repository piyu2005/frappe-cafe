import { useCall } from 'frappe-ui'

export const unreadMessageCount = useCall({
  url: '/api/v2/method/my_new_app.chat.unread_message_count',
})
