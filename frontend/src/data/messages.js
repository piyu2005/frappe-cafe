import { useCall } from 'frappe-ui'

export const unreadMessageCount = useCall({
  url: '/api/v2/method/cafe.chat.unread_message_count',
})
