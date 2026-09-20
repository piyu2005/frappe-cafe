import './island.css'

import Messages from '@/pages/Messages.vue'
import { mountIsland, whenReady } from './host'

// Messages of the Vue app, run inside a Builder page (see host.js). Each
// conversation gets a history entry, so Back goes to the one before.
function address(root) {
  const path = location.pathname.replace(/\/+$/, '')
  if (/^\/messages(\/|$)/.test(path)) return path
  // Not at Messages' own address, as in Builder's Preview.
  const conversation = root.getAttribute('data-conversation')
  return conversation ? `/messages/${encodeURIComponent(conversation)}` : '/messages'
}

whenReady(() => {
  const root = document.getElementById('mna-chat-root')
  if (!root) return
  mountIsland({
    root,
    page: { name: 'Messages', path: '/messages/:conversationId?', component: Messages },
    others: [['Home', '/'], ['Profile', '/profile/:userId?'], ['PostDetail', '/posts/:postId']],
    push: true,
    address,
  })
})
