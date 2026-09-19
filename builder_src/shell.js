// Behaviour of the shared app shell (rail, bottom bar, logo menu).
// Builder runs client scripts before the page data and CSRF token exist, so
// everything that needs them runs inside event handlers or after DOMContentLoaded.
// API calls use location.origin because Builder's editor Preview adds a <base href>
// that can point at another origin (the site's host_name).
(function () {
  'use strict'

  var NAV_PATHS = {
    home: function (p) { return p === '/' },
    search: function (p) { return p === '/search' || p.indexOf('/search/') === 0 },
    messages: function (p) { return p.indexOf('/messages') === 0 },
    profile: function (p) { return p.indexOf('/profile') === 0 },
    settings: function (p) { return p.indexOf('/settings') === 0 },
  }

  function markActiveNav() {
    var path = location.pathname.replace(/\/+$/, '') || '/'
    document.querySelectorAll('[data-nav]').forEach(function (el) {
      var active = NAV_PATHS[el.getAttribute('data-nav')](path)
      el.classList.toggle('active', active)
      if (active) el.setAttribute('aria-current', 'page')
    })
  }

  function showUnreadBadge() {
    fetch(location.origin + '/api/v2/method/my_new_app.chat.unread_message_count', { credentials: 'same-origin' })
      .then(function (r) { return r.ok ? r.json() : null })
      .then(function (body) {
        var count = body && body.data
        if (!count) return
        document.querySelectorAll('[data-badge="messages"]').forEach(function (el) {
          el.textContent = count > 99 ? '99+' : String(count)
          el.classList.add('show')
        })
      })
      .catch(function () {})
  }

  function setupLogoMenu() {
    var logo = document.getElementById('mna-logo')
    var menu = document.getElementById('mna-menu')
    if (!logo || !menu) return

    function setOpen(open) {
      menu.classList.toggle('open', open)
      logo.setAttribute('aria-expanded', open ? 'true' : 'false')
    }
    logo.addEventListener('click', function (e) {
      e.stopPropagation()
      setOpen(!menu.classList.contains('open'))
    })
    document.addEventListener('click', function (e) {
      if (!menu.contains(e.target)) setOpen(false)
    })
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') setOpen(false)
    })

    var logoutButton = document.getElementById('mna-logout')
    if (logoutButton) {
      logoutButton.addEventListener('click', function () {
        setOpen(false)
        confirmLogout()
      })
    }
  }

  function el(tag, className, text) {
    var node = document.createElement(tag)
    if (className) node.className = className
    if (text) node.textContent = text
    return node
  }

  function confirmLogout() {
    var overlay = el('div', 'mna-overlay')
    var dialog = el('div', 'mna-dialog')
    dialog.setAttribute('role', 'dialog')
    dialog.setAttribute('aria-modal', 'true')
    dialog.appendChild(el('h2', '', 'Log out?'))
    dialog.appendChild(el('p', '', 'You can always log back in.'))

    var actions = el('div', 'mna-dialog-actions')
    var cancel = el('button', 'mna-btn mna-btn-subtle', 'Cancel')
    var confirm = el('button', 'mna-btn mna-btn-solid', 'Log out')
    actions.appendChild(cancel)
    actions.appendChild(confirm)
    dialog.appendChild(actions)
    overlay.appendChild(dialog)
    document.body.appendChild(overlay)
    confirm.focus()

    function close() {
      overlay.remove()
      document.removeEventListener('keydown', onKey)
    }
    function onKey(e) {
      if (e.key === 'Escape') close()
    }
    document.addEventListener('keydown', onKey)
    cancel.addEventListener('click', close)
    overlay.addEventListener('click', function (e) {
      if (e.target === overlay) close()
    })
    confirm.addEventListener('click', function () {
      confirm.disabled = true
      fetch(location.origin + '/api/method/logout', {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'X-Frappe-CSRF-Token': (window.frappe && window.frappe.csrf_token) || '' },
      }).finally(function () {
        location.assign('/login')
      })
    })
  }

  document.addEventListener('DOMContentLoaded', function () {
    markActiveNav()
    setupLogoMenu()
    showUnreadBadge()
  })
})()
