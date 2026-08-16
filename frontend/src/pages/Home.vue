<template>
  <PageHeader v-if="!isMobile">
    <Breadcrumbs :items="[{ label: APP_NAME, route: '/' }, { label: 'Explore' }]" />
    <Button variant="solid" theme="gray" icon-left="lucide-plus" label="New Post" route="/write" />
  </PageHeader>
  <ScrollArea class="h-full">
    <!-- Mobile-only header bar rendered in normal flow (not through
         PageHeaderMobile's teleport) so it scrolls away with the rest of the
         page instead of staying fixed at the top. Sits outside the padded
         content wrapper below so it stays flush with the top of the screen,
         while still living inside ScrollArea so it scrolls with everything else. -->
    <div
      v-if="isMobile"
      class="flex h-[52px] items-center justify-between border-b border-outline-gray-1 px-4"
    >
      <div class="flex items-center gap-1.5">
        <span class="lucide-feather size-5 text-ink-gray-9" aria-hidden="true" />
        <span class="text-xl font-semibold text-ink-gray-9">{{ APP_NAME }}</span>
      </div>
      <div class="flex items-center gap-1">
        <button
          type="button"
          class="relative flex size-9 items-center justify-center text-ink-gray-6"
          @click="notificationsOpen = true"
        >
          <span class="lucide-bell size-5" aria-hidden="true" />
          <Badge v-if="unreadNotifCount.data" variant="solid" theme="red" size="sm" class="absolute -right-0.5 -top-0.5">
            {{ unreadNotifCount.data }}
          </Badge>
        </button>
        <Button variant="solid" theme="gray" icon="lucide-plus" route="/write" />
      </div>
    </div>

    <div class="mx-auto max-w-[760px] px-4 py-4 sm:px-5 sm:py-6">
      <div v-if="!myPostCount.loading && myPostCount.data === 0" class="mb-4 text-p-sm text-ink-gray-6">
        You haven't written anything yet.
        <router-link to="/write" class="text-ink-gray-9 underline">Write your first blog.</router-link>
      </div>

      <h1 class="font-serif text-xl font-medium text-ink-gray-9 sm:text-7xl">Writings from people on {{ APP_NAME }}</h1>

      <TextInput
        v-model="searchQuery"
        class="mt-5"
        placeholder="Search"
        size="lg"
      >
        <template #prefix>
          <span class="lucide-search size-4 text-ink-gray-5" aria-hidden="true" />
        </template>
      </TextInput>

      <LoadingText v-if="posts.loading && !posts.data" class="mt-10" :lines="4" />

      <div v-else-if="!posts.data || posts.data.length === 0" class="py-16 text-center">
        <p class="text-p-base text-ink-gray-6">No writings found.</p>
      </div>

      <div v-else class="mt-6 divide-y divide-outline-gray-1">
        <router-link
          v-for="post in posts.data"
          :key="post.name"
          :to="{ name: 'PostDetail', params: { postId: post.name } }"
          class="flex items-stretch justify-between gap-4 py-5"
        >
          <div class="flex min-w-0 flex-1 flex-col justify-between">
            <div>
              <div class="flex items-center gap-2">
                <Avatar :label="post.author_name || post.author" size="sm" />
                <span class="text-sm text-ink-gray-7">{{ post.author_name || post.author }}</span>
              </div>
              <div class="mt-2 text-lg-semibold text-ink-gray-9">
                {{ post.display_title || post.title || excerpt(post.content, 60) }}
              </div>
              <p class="mt-1 line-clamp-2 text-p-sm text-ink-gray-6">
                {{ post.excerpt || excerpt(post.content, 160) }}
              </p>
            </div>
            <div class="mt-2 text-xs text-ink-gray-5">
              {{ formatDate(post.creation) }} · {{ readTime(post.content) }} min read ·
              {{ commentCounts.data?.[post.name] ?? 0 }} comment{{ (commentCounts.data?.[post.name] ?? 0) === 1 ? '' : 's' }}
            </div>
          </div>
          <img
            v-if="coverImageFor(post)"
            :src="coverImageFor(post)"
            class="h-20 w-24 shrink-0 rounded-md object-cover"
          />
        </router-link>
      </div>

      <!-- No button: the sentinel below is watched by an IntersectionObserver
           that bumps pageLength itself once it scrolls into view, so more
           posts just keep appearing as the user scrolls. -->
      <div ref="loadMoreSentinelRef" class="h-1" />
      <p
        v-if="posts.data && posts.data.length && posts.hasNextPage && posts.loading"
        class="mt-6 text-center text-sm text-ink-gray-5"
      >
        Loading more...
      </p>
    </div>
  </ScrollArea>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  Avatar,
  Badge,
  Breadcrumbs,
  Button,
  LoadingText,
  PageHeader,
  ScrollArea,
  TextInput,
  useCall,
  useList,
} from 'frappe-ui'
import { session } from '@/data/session'
import { APP_NAME } from '@/utils/appName'
import { notificationsOpen, unreadNotifCount } from '@/data/notifications'
import { useIsMobile } from '@/composables/useIsMobile'

const isMobile = useIsMobile()

const searchQuery = ref('')
const pageLength = ref(10)

const filters = computed(() => {
  const f = { status: 'Published' }
  if (searchQuery.value) f.title = ['like', `%${searchQuery.value}%`]
  return f
})

const posts = useList({
  doctype: 'Post',
  fields: [
    'name',
    'title',
    'display_title',
    'content',
    'excerpt',
    'post_type',
    'attachment',
    'cover_image',
    'author',
    'author_name',
    'author_image',
    'creation',
  ],
  orderBy: 'creation desc',
  filters,
  limit: pageLength,
  refetch: true,
})

// Infinite scroll: a sentinel just past the last post is watched instead of
// a "Load more" button — once it scrolls into view, bump pageLength the same
// way the button used to on click. `root: null` (the browser viewport)
// rather than trying to target a specific scroll container — this page's
// content actually sits inside *two* nested ScrollAreas (this page's own,
// plus DesktopShell's own wrapper around all page content, which is the one
// that actually scrolls), and viewport-relative intersection tracks
// visibility correctly either way without needing to know which of the two
// is the real one.
const loadMoreSentinelRef = ref(null)
let loadMoreObserver = null

function canLoadMore() {
  return Boolean(posts.data && posts.data.length && posts.hasNextPage && !posts.loading)
}

onMounted(async () => {
  await nextTick()
  if (!loadMoreSentinelRef.value) return
  loadMoreObserver = new IntersectionObserver(
    (entries) => {
      if (entries[0]?.isIntersecting && canLoadMore()) {
        pageLength.value += 10
      }
    },
    { rootMargin: '400px' },
  )
  loadMoreObserver.observe(loadMoreSentinelRef.value)
})

onBeforeUnmount(() => {
  loadMoreObserver?.disconnect()
})

const commentCounts = useCall({
  url: '/api/v2/method/my_new_app.api.get_comment_counts',
  method: 'POST',
  immediate: false,
})

watch(
  () => posts.data,
  (data) => {
    if (data && data.length) commentCounts.submit({ posts: data.map((p) => p.name) })
  },
)

watch(searchQuery, () => {
  pageLength.value = 10
})

const myPostCount = useCall({
  url: '/api/v2/method/frappe.client.get_count',
  params: { doctype: 'Post', filters: JSON.stringify({ author: session.user }) },
})

function stripHtml(html) {
  const div = document.createElement('div')
  div.innerHTML = html || ''
  return div.textContent || div.innerText || ''
}

function excerpt(content, length) {
  const text = stripHtml(content).trim()
  return text.length > length ? text.slice(0, length) + '…' : text
}

function coverImageFor(post) {
  if (post.cover_image) return post.cover_image
  if (post.post_type !== 'Video') return post.attachment
  return null
}

function readTime(content) {
  const words = stripHtml(content).trim().split(/\s+/).filter(Boolean).length
  return Math.max(1, Math.round(words / 200))
}

function formatDate(value) {
  if (!value) return ''
  return new Date(value).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}
</script>
