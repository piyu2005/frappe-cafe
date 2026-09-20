import { createApp, h } from 'vue'
import { RouterView, createMemoryHistory, createRouter } from 'vue-router'
import { FrappeUI, FrappeUIProvider } from 'frappe-ui'

// Runs one page of the Vue app inside a Builder page. The page is used as it
// is, and it talks to a router of its own. This router lives in memory: a
// move to any route that is not the page itself is a real page load, so the
// Builder pages take over, and the address bar follows the page when it moves
// between its own routes (a new draft, another conversation).
const NOT_HERE = { render: () => null }

// Builder's Preview adds a <base href> for the site's host_name, which can be
// another origin than the one this page runs on (the Vite dev server); the
// page's requests are relative, so they are pointed back at this origin.
function useThisOrigin() {
  const base = document.querySelector('base[href]')
  if (base && new URL(base.href).origin !== location.origin) base.href = location.origin + '/'
}

// `page` is { name, path, component }; `others` are the names of other routes
// the page links to. `push` keeps a history entry for each of the page's own
// moves (a chat's conversations), instead of replacing the address.
export function mountIsland({ root, page, others = [], push = false, address }) {
  useThisOrigin()
  // frappe-ui reads the CSRF token from here, as the Vue app's page does.
  window.csrf_token = (window.frappe && window.frappe.csrf_token) || window.csrf_token
  const routes = [
    { path: page.path, name: page.name, component: page.component },
    ...others.map(([name, path]) => ({ path, name, component: NOT_HERE })),
    // Any other address a link points at is a page load too.
    { path: '/:rest(.*)*', name: 'Elsewhere', component: NOT_HERE },
  ]
  const router = createRouter({ history: createMemoryHistory(), routes })
  // How the page moved: push and replace differ for the address bar, and a move
  // that follows Back or Forward must not add an entry.
  let how = 'replace'
  let following = false
  for (const method of ['push', 'replace']) {
    const original = router[method].bind(router)
    router[method] = (to) => {
      how = following ? 'follow' : method
      following = false
      return original(to)
    }
  }
  const inFrame = window.top !== window // Builder's Preview is not at the page's address
  router.beforeEach((to, from) => {
    if (from.name && to.name !== page.name) {
      window.location.assign(to.fullPath)
      return false
    }
  })
  router.afterEach((to, from) => {
    if (to.name !== page.name || inFrame || !from.name || how === 'follow') return
    if (push && how === 'push') history.pushState(null, '', to.fullPath)
    else history.replaceState(null, '', to.fullPath)
  })
  // The provider is what shows toasts and confirm dialogs.
  const app = createApp({ render: () => h(FrappeUIProvider, null, () => h(RouterView)) })
  app.use(router)
  app.use(FrappeUI, { socketio: false })
  // Back and Forward move between the page's own addresses.
  if (push) {
    window.addEventListener('popstate', () => {
      following = true
      router.replace(address(root))
    })
  }
  router.replace(address(root)).then(() => app.mount(root))
}

export function whenReady(start) {
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start)
  else start()
}
