import './island.css'

import WritePost from '@/pages/WritePost.vue'
import { mountIsland, whenReady } from './host'

// The post editor of the Vue app, run inside a Builder page (see host.js).
function address(root) {
  const postId = root.getAttribute('data-post')
  return postId ? `/write/${encodeURIComponent(postId)}` : '/write'
}

whenReady(() => {
  const root = document.getElementById('mna-write-root')
  if (!root) return
  mountIsland({
    root,
    page: { name: 'WritePost', path: '/write/:postId?', component: WritePost },
    others: [['Home', '/'], ['Profile', '/profile/:userId?'], ['PostDetail', '/posts/:postId']],
    address,
  })
})
