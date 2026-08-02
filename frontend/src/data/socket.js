import { initSocket } from 'frappe-ui'

let socket = null

export function getSocket() {
  if (!socket) {
    socket = initSocket()
  }
  return socket
}
