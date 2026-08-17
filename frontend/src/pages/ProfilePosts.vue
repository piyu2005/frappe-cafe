<template>
  <PageHeader v-if="!isMobile">
    <Breadcrumbs :items="breadcrumbItems" />
  </PageHeader>
  <PageHeaderMobile v-else :title="profile.data?.full_name ? `${profile.data.full_name}'s posts` : 'Posts'">
    <template #left>
      <PageHeaderBackButton :to="{ name: 'Profile', params: { userId: targetUser } }" />
    </template>
    <template #right>
      <MobileNotificationBell />
    </template>
  </PageHeaderMobile>

  <ScrollArea class="h-[calc(100vh-52px)] md:h-[calc(100vh-3rem)]">
    <div class="mx-auto max-w-[760px] px-5 py-8">
      <div class="flex items-center gap-3">
        <Avatar :image="profile.data?.user_image" :label="profile.data?.full_name" size="lg" />
        <div>
          <h1 class="text-xl font-semibold text-ink-gray-9">{{ profile.data?.full_name }}'s posts</h1>
          <router-link
            :to="{ name: 'Profile', params: { userId: targetUser } }"
            class="text-sm text-ink-gray-5 hover:underline"
          >
            ← Back to profile
          </router-link>
        </div>
      </div>

      <div class="mt-6 flex flex-wrap items-center gap-3">
        <FormControl
          v-model="categoryFilter"
          type="select"
          class="w-48"
          :options="categoryOptions"
        />
        <div v-if="isOwnProfile" class="flex items-center gap-1 rounded-md bg-surface-gray-2 p-0.5">
          <button
            v-for="f in statusFilters"
            :key="f.value"
            class="rounded px-2 py-1 text-xs"
            :class="statusFilter === f.value ? 'bg-surface-base text-ink-gray-9 shadow-sm' : 'text-ink-gray-5'"
            @click="statusFilter = f.value"
          >
            {{ f.label }}
          </button>
        </div>
      </div>

      <LoadingText v-if="posts.loading && !posts.data" class="mt-8" :lines="6" />
      <p v-else-if="!posts.data || !posts.data.length" class="mt-10 text-center text-p-sm text-ink-gray-5">
        No posts match these filters.
      </p>

      <div v-else class="mt-6 divide-y divide-outline-gray-1">
        <router-link
          v-for="post in posts.data"
          :key="post.name"
          :to="
            post.status === 'Published'
              ? { name: 'PostDetail', params: { postId: post.name } }
              : { name: 'WritePost', params: { postId: post.name } }
          "
          class="flex items-start justify-between gap-4 py-5"
        >
          <div class="min-w-0 flex-1">
            <div class="flex items-center gap-2">
              <Avatar :image="post.author_image" :label="post.author_name || post.author" size="sm" />
              <span class="text-sm text-ink-gray-7">{{ post.author_name || post.author }}</span>
            </div>
            <div class="mt-2 flex items-center gap-2">
              <div class="text-lg-semibold text-ink-gray-9">{{ post.display_title || post.title || excerpt(post.content, 60) }}</div>
              <Badge v-if="post.status !== 'Published'" :label="post.status" variant="subtle" theme="gray" size="sm" />
            </div>
            <p class="mt-1 line-clamp-2 text-p-sm text-ink-gray-6">{{ post.excerpt || excerpt(post.content, 160) }}</p>
            <div class="mt-2 text-xs text-ink-gray-5">
              {{ formatDate(post.creation) }} · {{ readTime(post.content) }} min read
            </div>
          </div>
          <!-- 1.91:1 matches StoryPreviewDialog's cover-image crop ratio -->
          <img
            v-if="thumbnailFor(post)"
            :src="thumbnailFor(post)"
            class="aspect-[1.91/1] w-24 shrink-0 rounded-md object-cover"
          />
        </router-link>
      </div>
    </div>
  </ScrollArea>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import {
  Avatar,
  Badge,
  Breadcrumbs,
  FormControl,
  LoadingText,
  PageHeader,
  PageHeaderBackButton,
  PageHeaderMobile,
  ScrollArea,
  useCall,
  useList,
} from 'frappe-ui'
import { session } from '@/data/session'
import { APP_NAME } from '@/utils/appName'
import MobileNotificationBell from '@/components/MobileNotificationBell.vue'
import { useIsMobile } from '@/composables/useIsMobile'

const isMobile = useIsMobile()

const route = useRoute()
const targetUser = computed(() => route.params.userId || session.user)
const isOwnProfile = computed(() => targetUser.value === session.user)

const profile = useCall({
  url: '/api/v2/method/my_new_app.api.get_profile',
  params: () => ({ user: targetUser.value }),
})

const categoryList = useCall({
  url: '/api/v2/method/my_new_app.api.list_categories',
})

const categoryOptions = computed(() => [
  { label: 'All categories', value: '' },
  ...(categoryList.data || []).map((c) => ({ label: c.title, value: c.name })),
])

const statusFilters = [
  { label: 'Published', value: 'Published' },
  { label: 'Drafts', value: 'Draft' },
  { label: 'Archived', value: 'Archived' },
]
const statusFilter = ref('Published')
const categoryFilter = ref('')

const filters = computed(() => {
  const f = { author: targetUser.value, status: isOwnProfile.value ? statusFilter.value : 'Published' }
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
    'cover_image',
    'attachment',
    'status',
    'creation',
    'author',
    'author_name',
    'author_image',
  ],
  filters,
  orderBy: 'creation desc',
  limit: 60,
  refetch: true,
})

function thumbnailFor(post) {
  if (post.cover_image) return post.cover_image
  if (post.post_type === 'Image') return post.attachment
  return null
}

function stripHtml(html) {
  const div = document.createElement('div')
  div.innerHTML = html || ''
  return div.textContent || div.innerText || ''
}

function excerpt(content, length) {
  const text = stripHtml(content).trim()
  return text.length > length ? text.slice(0, length) + '…' : text
}

function readTime(content) {
  const words = stripHtml(content).trim().split(/\s+/).filter(Boolean).length
  return Math.max(1, Math.round(words / 200))
}

function formatDate(value) {
  if (!value) return ''
  return new Date(value).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
}

const breadcrumbItems = computed(() => [
  { label: APP_NAME, route: '/' },
  { label: profile.data?.full_name || 'Profile', route: `/profile/${targetUser.value}` },
  { label: 'Posts' },
])
</script>
