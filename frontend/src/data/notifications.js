import { ref } from 'vue'
import { useCall } from 'frappe-ui'

export const unreadNotifCount = useCall({
  url: '/api/v2/method/my_new_app.follow.unread_notification_count',
})

// Shared so both AppLayout (which owns the bell in the desktop rail/sidebar
// and renders the panel itself) and individual pages (which show the bell
// next to "+ New Post" in their mobile header) can toggle the same panel.
export const notificationsOpen = ref(false)
