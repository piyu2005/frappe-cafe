import { io } from 'socket.io-client'

let socket = null

// frappe-ui's own initSocket() derives the realtime namespace from
// window.location.hostname in dev mode — which is wrong here whenever the
// app is opened via plain "localhost" instead of this bench's actual site,
// "mynewsite.localhost". The realtime server resolves the site from the
// same hostname on its end (falling back to the bench's *default* site,
// which isn't this one, for bare "localhost"/"127.0.0.1"), so a mismatched
// namespace gets the connection rejected outright — the "WebSocket closed
// before the connection is established" error. Hardcoding the real site
// name in dev sidesteps this regardless of which hostname the browser used.
export function getSocket() {
  if (!socket) {
    const siteName = import.meta.env.DEV ? 'mynewsite.localhost' : window.site_name
    const port = window.location.port ? ':9000' : ''
    const protocol = port ? 'http' : 'https'
    const url = `${protocol}://${window.location.hostname}${port}/${siteName}`
    socket = io(url, { withCredentials: true })
  }
  return socket
}
