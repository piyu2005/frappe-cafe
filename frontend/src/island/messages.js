// The unread count sits in the Builder page's rail; its script refreshes it.
export const unreadMessageCount = {
  reload() {
    window.MNA?.refreshBadges?.()
  },
}
