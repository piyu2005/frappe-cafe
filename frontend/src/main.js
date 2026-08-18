import './index.css'

import { createApp } from 'vue'
import { FrappeUI } from 'frappe-ui'
import router from './router'
import App from './App.vue'

let app = createApp(App)

app.use(router)
// socketio: false — the app manages its own realtime connection via
// data/socket.js's getSocket() (used for chat/notification events), which
// works correctly regardless of which hostname the dev server was opened
// through. frappe-ui's own auto-connected socket derives its namespace from
// window.location.hostname and isn't used anywhere ($socket is never
// referenced), so it's just a second, redundant connection that hits the
// same hostname/namespace mismatch this app already works around.
app.use(FrappeUI, { socketio: false })

app.mount('#app')

// Tooltips (and similar hover UI) can reappear "on their own" after
// switching tabs/apps and back, for two independent reasons that both need
// handling:
// 1. Focus: clicking a nav link (e.g. a rail icon) to navigate leaves it
//    keyboard-focused in an SPA — there's no full page load to reset focus.
//    Accessible tooltips open on focus as well as hover, and focus doesn't
//    clear just because the tab lost visibility, so the still-focused
//    element's tooltip can (re)open purely from the window regaining focus.
// 2. Hover: the cursor doesn't move when switching tabs without touching the
//    mouse, so if it was left resting over a hoverable element, the browser
//    still counts it as hovered on return — and if a hover-delay timer was
//    mid-flight when the tab backgrounded, background-tab timer throttling
//    can make it fire late, right as focus returns.
function dismissFloatingUI() {
  document.activeElement?.blur?.()

  const hovered = document.querySelectorAll(':hover')
  for (let i = hovered.length - 1; i >= 0; i--) {
    const el = hovered[i]
    el.dispatchEvent(new PointerEvent('pointerleave', { bubbles: false, cancelable: true }))
    el.dispatchEvent(new PointerEvent('pointerout', { bubbles: true, cancelable: true }))
    el.dispatchEvent(new MouseEvent('mouseleave', { bubbles: false, cancelable: true }))
    el.dispatchEvent(new MouseEvent('mouseout', { bubbles: true, cancelable: true }))
  }

  // Escape is the accessibility-mandated way to dismiss floating UI
  // (tooltips/popovers/menus) — a backstop for anything the above missed.
  // But it's indistinguishable, to any listener, from a real Escape press —
  // and frappe-ui's actual <Dialog> modals (CreateGroupDialog,
  // GroupMembersDialog, StoryPreviewDialog, etc. all use it) close on
  // Escape too. Firing this while one's open would silently close it the
  // moment the tab loses visibility, so it'd just be gone by the time the
  // user comes back. `.dialog-content` is the class frappe-ui's Dialog.vue
  // renders only while a dialog is actually open — skip the synthetic key
  // there so a real modal survives a tab switch.
  if (!document.querySelector('.dialog-content')) {
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true, cancelable: true }))
  }
}

document.addEventListener('visibilitychange', () => {
  dismissFloatingUI()
  if (document.visibilityState !== 'visible') return
  document.body.style.pointerEvents = 'none'
  const restore = () => {
    document.body.style.pointerEvents = ''
    window.removeEventListener('mousemove', restore)
  }
  window.addEventListener('mousemove', restore, { passive: true })
})

// visibilitychange only fires for tab switches within the browser; blur/focus
// also cover switching to a different application entirely.
window.addEventListener('blur', dismissFloatingUI)
