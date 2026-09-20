import { io } from 'socket.io-client'

// The live-updates connection. The Vue app takes the site's name from its own
// page; a Builder page has none, and the site's name is its address.
let socket = null

export function getSocket() {
  if (!socket) {
    const port = window.location.port ? ':9000' : ''
    const protocol = port ? 'http' : 'https'
    socket = io(`${protocol}://${window.location.hostname}${port}/${window.location.hostname}`, { withCredentials: true })
  }
  return socket
}
