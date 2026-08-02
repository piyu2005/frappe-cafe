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

export async function login(email, password) {
  await call('login', { usr: email, pwd: password })
  session.refresh()
}

export async function logout() {
  await call('logout')
  session.refresh()
}
