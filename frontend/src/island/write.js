import './island.css'

import { createApp, h } from 'vue'
import { RouterView, createMemoryHistory, createRouter } from 'vue-router'
import { FrappeUI, FrappeUIProvider } from 'frappe-ui'
import WritePost from '@/pages/WritePost.vue'

// The post editor of the Vue app, run inside a Builder page. WritePost.vue is
// used as it is, and it talks to a router of its own. This router lives in
// memory: a move to any page other than the editor is a real page load, so
// the Builder pages take over, and the address bar follows the editor when
// it changes the post (a new draft gets its id in the address).
const NOT_HERE = { render: () => null }
const routes = [
  { path: '/write/:postId?', name: 'WritePost', component: WritePost },
  { path: '/', name: 'Home', component: NOT_HERE },
  { path: '/profile/:userId?', name: 'Profile', component: NOT_HERE },
  { path: '/posts/:postId', name: 'PostDetail', component: NOT_HERE },
]

// Builder's Preview adds a <base href> for the site's host_name, which can be
// another origin than the one this page runs on (the Vite dev server); the
// editor's requests are relative, so they are pointed back at this origin.
function useThisOrigin() {
  const base = document.querySelector('base[href]')
  if (base && new URL(base.href).origin !== location.origin) base.href = location.origin + '/'
}

function start(root) {
  useThisOrigin()
  // frappe-ui reads the CSRF token from here, as the Vue app's page does.
  window.csrf_token = (window.frappe && window.frappe.csrf_token) || window.csrf_token
  const router = createRouter({ history: createMemoryHistory(), routes })
  router.beforeEach((to, from) => {
    if (from.name && to.name !== 'WritePost') {
      window.location.assign(to.fullPath)
      return false
    }
  })
  router.afterEach((to) => {
    // Not inside Builder's Preview frame, which is not at the editor's address.
    if (to.name === 'WritePost' && window.top === window) history.replaceState(null, '', to.fullPath)
  })
  // The provider is what shows toasts and confirm dialogs.
  const app = createApp({ render: () => h(FrappeUIProvider, null, () => h(RouterView)) })
  app.use(router)
  app.use(FrappeUI, { socketio: false })
  const postId = root.getAttribute('data-post')
  router.replace(postId ? `/write/${encodeURIComponent(postId)}` : '/write').then(() => app.mount(root))
}

window.MnaWrite = { start }
function autoStart() {
  const root = document.getElementById('mna-write-root')
  if (root) start(root)
}
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', autoStart)
else autoStart()
