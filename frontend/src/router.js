import { createRouter, createWebHistory } from 'vue-router'
import { session, verifySession } from '@/data/session'
import { settingsOpen } from '@/data/settings'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/pages/Login.vue'),
  },
  {
    path: '/signup',
    name: 'Signup',
    component: () => import('@/pages/Signup.vue'),
  },
  {
    path: '/',
    component: () => import('@/components/AppLayout.vue'),
    children: [
      {
        path: '',
        name: 'Home',
        component: () => import('@/pages/Home.vue'),
      },
      {
        path: 'profile/:userId?',
        name: 'Profile',
        component: () => import('@/pages/Profile.vue'),
      },
      {
        path: 'profile/:userId?/posts',
        name: 'ProfilePosts',
        component: () => import('@/pages/ProfilePosts.vue'),
      },
      {
        path: 'settings',
        name: 'Settings',
        // Settings is a modal, not a page. Opening /settings shows it over
        // the current page, or over Home on a direct load.
        component: { render: () => null },
        beforeEnter: (to, from) => {
          settingsOpen.value = true
          return from.name ? false : { name: 'Home' }
        },
      },
      {
        path: 'write/:postId?',
        name: 'WritePost',
        component: () => import('@/pages/WritePost.vue'),
      },
      {
        path: 'posts/:postId',
        name: 'PostDetail',
        component: () => import('@/pages/PostDetail.vue'),
      },
      {
        path: 'search',
        name: 'SearchPeople',
        component: () => import('@/pages/SearchPeople.vue'),
      },
      {
        path: 'publications/:handle',
        name: 'PublicationDetail',
        component: () => import('@/pages/PublicationDetail.vue'),
      },
      {
        path: 'publications/:handle/members',
        name: 'PublicationMembers',
        component: () => import('@/pages/PublicationMembers.vue'),
      },
      {
        path: 'messages/:conversationId?',
        name: 'Messages',
        component: () => import('@/pages/Messages.vue'),
      },
    ],
  },
]

let router = createRouter({
  history: createWebHistory('/'),
  routes,
})

// Shared with main.js's visibilitychange handler — both need the same
// definition of "a page a logged-out visitor is allowed to sit on" so a
// stale-session revalidation on tab-focus can't disagree with what
// navigating there directly would have decided.
export const GUEST_ROUTE_NAMES = ['Login', 'Signup']

router.beforeEach(async (to) => {
  let isGuestPage = GUEST_ROUTE_NAMES.includes(to.name)
  let bounceIfLoggedIn = isGuestPage

  // The fast, synchronous-cookie-only path is only safe for the specific
  // case of a guest page where the cookie *also* says logged out — skipping
  // the round-trip there just means a genuinely logged-in visitor (missing
  // cookie) briefly sees the login form instead of an auto-redirect, not
  // worth a network round-trip (and the blank-screen wait for it) on every
  // single /login or /signup load. It would NOT be safe to also skip this
  // for a guest page where the cookie says logged in: redirecting to Home
  // on that alone risks bouncing straight back to Login a moment later once
  // a protected route's own verifySession() call discovers the cookie was
  // stale — a visible Login → Home → Login flicker.
  if (isGuestPage && !session.isLoggedIn) {
    return
  }

  // Only the very first navigation needs to wait on this — verifySession()
  // resolves once and caches its promise, so every later navigation reads
  // the already-settled session.isLoggedIn synchronously as before.
  await verifySession()

  if (!session.isLoggedIn && !isGuestPage) {
    return { name: 'Login', query: { redirect: to.fullPath } }
  }

  if (session.isLoggedIn && bounceIfLoggedIn) {
    return { name: 'Home' }
  }
})

// Clicking a nav link (e.g. a rail icon) to navigate leaves it focused —
// there's no full page load to reset focus like a normal link click would
// cause. Left focused, its tooltip can reopen later purely from the window
// regaining focus (e.g. after switching tabs), with no hover involved.
router.afterEach(() => {
  document.activeElement?.blur?.()
})

export default router
