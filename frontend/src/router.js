import { createRouter, createWebHistory } from 'vue-router'
import { session, verifySession } from '@/data/session'

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
        component: () => import('@/pages/Settings.vue'),
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
  history: createWebHistory('/frontend'),
  routes,
})

router.beforeEach(async (to) => {
  // Only the very first navigation needs to wait on this — verifySession()
  // resolves once and caches its promise, so every later navigation reads
  // the already-settled session.isLoggedIn synchronously as before.
  await verifySession()

  let isGuestPage = to.name === 'Login' || to.name === 'Signup'

  if (!session.isLoggedIn && !isGuestPage) {
    return { name: 'Login', query: { redirect: to.fullPath } }
  }

  if (session.isLoggedIn && isGuestPage) {
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
