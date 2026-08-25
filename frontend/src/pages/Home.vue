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
        <MobileNotificationBell />
        <Button variant="solid" theme="gray" icon="lucide-plus" route="/write" />
      </div>
    </div>

    <div class="mx-auto max-w-[640px] px-4 py-4 sm:px-5 sm:py-6">
      <div v-if="!myPostCount.loading && myPostCount.data === 0" class="mb-6 text-lg text-ink-gray-5">
        You haven't written anything yet.
        <router-link to="/write" class="text-lg-medium text-ink-gray-8 underline">Write your first blog.</router-link>
      </div>

      <h1 class="font-[Newsreader] text-[32px] font-medium leading-[1.5] tracking-[0.005em] text-ink-gray-8">
        Writings from people on {{ APP_NAME }}
      </h1>

      <TextInput v-model="searchQuery" class="mt-4" placeholder="Search" variant="subtle" size="sm">
        <template #prefix>
          <span class="lucide-search size-4 text-ink-gray-5" aria-hidden="true" />
        </template>
      </TextInput>

      <div class="mt-4 flex flex-wrap gap-2">
        <button
          v-for="cat in categoryList.data || []"
          :key="cat.name"
          type="button"
          class="rounded px-2 py-1.5 text-base text-ink-gray-7"
          :class="
            categoryFilter === cat.name
              ? 'bg-surface-gray-2'
              : 'border border-outline-gray-2 hover:bg-surface-gray-1'
          "
          @click="categoryFilter = categoryFilter === cat.name ? '' : cat.name"
        >
          {{ cat.title }}
          <span v-if="categoryFilter === cat.name" class="lucide-x ml-1 size-3" aria-hidden="true" />
        </button>
      </div>

      <LoadingText v-if="posts.loading && !posts.data" class="mt-10" :lines="4" />

      <div v-else-if="!posts.data || posts.data.length === 0" class="py-16 text-center">
        <p class="text-p-base text-ink-gray-6">No writings found.</p>
      </div>

      <div v-else class="mt-6 divide-y divide-outline-gray-1 space-y-12">
        <router-link
          v-for="post in posts.data"
          :key="post.name"
          :to="{ name: 'PostDetail', params: { postId: post.name } }"
          class="flex items-stretch justify-between gap-4 py-2"
        >
          <div class="flex min-w-0 flex-1 flex-col justify-between">
            <div>
              <div class="flex items-center gap-2">
                <Avatar :image="post.author_image" :label="post.author_name || post.author" size="sm" />
                <span class="text-sm text-ink-gray-8">{{ post.author_name || post.author }}</span>
              </div>
              <div class="mt-2 text-p-base-semibold text-ink-gray-8">
                {{ post.display_title || post.title || excerpt(post.content, 60) }}
              </div>
              <p class="mt-1 line-clamp-2 text-p-base text-ink-gray-6">
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
            class="h-24 w-32 shrink-0 rounded-md bg-surface-gray-2 object-cover"
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
import MobileNotificationBell from '@/components/MobileNotificationBell.vue'
import { useIsMobile } from '@/composables/useIsMobile'

const isMobile = useIsMobile()

const searchQuery = ref('')
const pageLength = ref(10)

const categoryList = useCall({
  url: '/api/v2/method/my_new_app.api.list_categories',
})
const categoryFilter = ref('')

const filters = computed(() => {
  const f = { status: 'Published' }
  if (searchQuery.value) f.title = ['like', `%${searchQuery.value}%`]
  if (categoryFilter.value) f.category = categoryFilter.value
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

watch([searchQuery, categoryFilter], () => {
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
