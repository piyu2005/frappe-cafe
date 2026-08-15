<template>
  <PageHeader v-if="!isMobile">
    <Breadcrumbs :items="[{ label: APP_NAME, route: '/' }, { label: 'Explore' }]" />
    <Button variant="solid" theme="gray" icon-left="lucide-plus" label="New Post" route="/write" />
  </PageHeader>
  <PageHeaderMobile v-else title="Explore">
    <template #right>
      <Button variant="solid" theme="gray" icon="lucide-plus" route="/write" />
    </template>
  </PageHeaderMobile>

  <ScrollArea class="h-full">
    <div class="mx-auto max-w-[760px] px-4 py-4 sm:px-5 sm:py-6">
      <div v-if="!myPostCount.loading && myPostCount.data === 0" class="mb-4 text-p-sm text-ink-gray-6">
        You haven't written anything yet.
        <router-link to="/write" class="text-ink-gray-9 underline">Write your first blog.</router-link>
      </div>

      <h1 class="text-3xl font-semibold text-ink-gray-9">Writings from people on {{ APP_NAME }}</h1>

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

      <button
        v-if="posts.data && posts.data.length && posts.hasNextPage"
        class="mt-6 block w-full text-center text-sm text-ink-gray-6 hover:text-ink-gray-9 hover:underline"
        :disabled="posts.loading"
        @click="pageLength += 10"
      >
        {{ posts.loading ? 'Loading...' : 'Load more' }}
      </button>
    </div>
  </ScrollArea>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import {
  Avatar,
  Breadcrumbs,
  Button,
  LoadingText,
  PageHeader,
  PageHeaderMobile,
  ScrollArea,
  TextInput,
  useCall,
  useList,
} from 'frappe-ui'
import { session } from '@/data/session'
import { APP_NAME } from '@/utils/appName'
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
