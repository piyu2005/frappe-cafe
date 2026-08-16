import { computed, reactive } from 'vue'
import { call } from 'frappe-ui'

function sessionUser() {
  let cookies = new URLSearchParams(document.cookie.split('; ').join('&'))
  let _sessionUser = cookies.get('user_id')
  if (!_sessionUser || _sessionUser === 'Guest') {
    _sessionUser = null
  }
  return _sessionUser
}

export const session = reactive({
  user: sessionUser(),
  isLoggedIn: computed(() => !!session.user),
  refresh() {
    session.user = sessionUser()
  },
})

// Frappe sets the real auth cookie (`sid`) with a long expiry, but the
// `user_id` cookie the check above reads is session-only (no Max-Age) — it
// can vanish (browser restart, long sleep, cookie cleanup) while the actual
// server-side session backing `sid` is still perfectly valid, making a
// genuinely logged-in user look logged-out and get bounced to the login
// page. Verifying against the server once on boot (the router guard calls
// this before its first navigation decision) catches that case instead of
// trusting the fragile cookie alone.
let verifyPromise = null
export function verifySession() {
  if (!verifyPromise) {
    verifyPromise = call('frappe.auth.get_logged_user')
      .then((user) => {
        session.user = user && user !== 'Guest' ? user : null
      })
      .catch((err) => {
        // A 401/403 here means whatever the client thought its session was
        // is no longer valid server-side — clearing session.user lets the
        // router guard redirect to Login cleanly, instead of leaving a
        // stale cookie value in place that looks logged-in but 403s on
        // every real request. Anything else (network blip, a 502 during a
        // deploy) is not evidence the session is actually invalid, so it's
        // left untouched rather than bouncing a genuinely logged-in user.
        if (err?.status === 401 || err?.status === 403) {
          session.user = null
        }
      })
  }
  return verifyPromise
}

export async function login(email, password) {
  await call('login', { usr: email, pwd: password })
  session.refresh()
}

export async function logout() {
  await call('logout')
  session.refresh()
}
