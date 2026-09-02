<template>
  <PageHeader v-if="!isMobile">
    <Breadcrumbs :items="breadcrumbItems" />
    <Button variant="solid" theme="gray" icon-left="lucide-plus" label="New Post" route="/write" />
  </PageHeader>
  <PageHeaderMobile v-else title="Posts">
    <template #left>
      <PageHeaderBackButton :to="{ name: 'Profile', params: { userId: targetUser } }" />
    </template>
    <template #right>
      <MobileNotificationBell />
    </template>
  </PageHeaderMobile>

  <ScrollArea class="h-full">
    <div class="mx-auto max-w-[600px] px-4 py-6 sm:px-5 sm:py-8">
      <LoadingText v-if="posts.loading && !posts.data" :lines="6" />

      <template v-else>
        <div class="flex items-center gap-2">
          <Button
            variant="subtle"
            theme="gray"
            size="sm"
            icon="lucide-arrow-left"
            label="Back to profile"
            :route="{ name: 'Profile', params: { userId: targetUser } }"
          />
          <h1 class="text-3xl-medium text-ink-gray-8">
            {{ isOwnProfile ? 'My Posts' : `Posts from ${profile.data?.full_name}` }}
          </h1>
        </div>

        <!-- Own profile gets Published/Drafts/Archived tabs - Saved stays
             exclusively under Settings (it's "posts I bookmarked", a
             different concept from "posts I wrote"). A visitor only ever
             sees the flat published list below; drafts/archived are private
             regardless of what UI is offered here, already enforced
             server-side by Post's own permission hooks. -->
        <Tabs v-if="isOwnProfile" v-model="tab" :tabs="ownTabs" class="mt-8 posts-tabs">
          <template #tab-panel="{ tab: activeTab }">
            <template v-if="activeTab.label === 'Published'">
              <div v-if="posts.data && posts.data.length" class="mt-4 divide-y divide-outline-gray-1">
                <router-link
                  v-for="post in posts.data"
                  :key="post.name"
                  :to="{ name: 'PostDetail', params: { postId: post.name } }"
                  class="flex items-stretch justify-between gap-4 py-5 first:pt-0 last:pb-0"
                >
                  <div class="flex min-w-0 flex-1 flex-col justify-between">
                    <div>
                      <div class="text-p-base-semibold text-ink-gray-8">{{ post.display_title || post.title || 'Untitled' }}</div>
                      <p class="mt-1 line-clamp-2 text-p-base text-ink-gray-6">{{ post.excerpt || excerpt(post.content, 140) }}</p>
                    </div>
                    <div class="mt-2 text-xs text-ink-gray-5">
                      {{ formatDate(post.creation) }} · {{ readTime(post.content) }} min read ·
                      {{ post.comment_count }} comment{{ post.comment_count === 1 ? '' : 's' }}
                    </div>
                  </div>
                  <img
                    v-if="thumbnailFor(post)"
                    :src="thumbnailFor(post)"
                    loading="lazy"
                    decoding="async"
                    class="h-20 w-24 shrink-0 rounded-md object-cover"
                  />
                </router-link>
              </div>
              <p v-else class="mt-6 text-base text-ink-gray-5">
                You haven't published anything yet.
                <router-link to="/write" class="text-base-medium text-ink-gray-8 underline">
                  Write your first blog.
                </router-link>
              </p>
            </template>

            <!-- Drafts/Archived: same source/row style as Settings.vue's own
                 tabs of the same name (author+status filtered Post list,
                 ordered by last-modified, linking to the editor rather than
                 the public post view since there's nothing public to see yet). -->
            <template v-else>
              <LoadingText v-if="draftArchivePosts.loading && !draftArchivePosts.data" class="mt-6" :lines="4" />
              <p
                v-else-if="!draftArchivePosts.data || draftArchivePosts.data.length === 0"
                class="mt-6 text-base text-ink-gray-5"
              >
                {{ activeTab.label === 'Drafts' ? "You don't have any drafts." : "You don't have any archived posts." }}
              </p>
              <div v-else class="mt-4 divide-y divide-outline-gray-1">
                <router-link
                  v-for="post in draftArchivePosts.data"
                  :key="post.name"
                  :to="{ name: 'WritePost', params: { postId: post.name } }"
                  class="flex items-stretch justify-between gap-4 py-5 first:pt-0 last:pb-0"
                >
                  <div class="min-w-0 flex-1">
                    <div class="text-p-base-semibold text-ink-gray-8">{{ post.display_title || post.title || 'Untitled' }}</div>
                    <p class="mt-1 line-clamp-2 text-p-base text-ink-gray-6">{{ post.excerpt || excerpt(post.content, 140) }}</p>
                    <div class="mt-2 text-xs text-ink-gray-5">{{ formatDate(post.modified) }}</div>
                  </div>
                  <img
                    v-if="thumbnailFor(post)"
                    :src="thumbnailFor(post)"
                    loading="lazy"
                    decoding="async"
                    class="h-20 w-24 shrink-0 rounded-md object-cover"
                  />
                </router-link>
              </div>
            </template>
          </template>
        </Tabs>

        <!-- Visitor view: unchanged flat published-only list, no tabs. -->
        <template v-else>
          <div v-if="posts.data && posts.data.length" class="mt-4 divide-y divide-outline-gray-1">
            <router-link
              v-for="post in posts.data"
              :key="post.name"
              :to="{ name: 'PostDetail', params: { postId: post.name } }"
              class="flex items-stretch justify-between gap-4 py-5 first:pt-0 last:pb-0"
            >
              <div class="flex min-w-0 flex-1 flex-col justify-between">
                <div>
                  <div class="text-p-base-semibold text-ink-gray-8">{{ post.display_title || post.title || 'Untitled' }}</div>
                  <p class="mt-1 line-clamp-2 text-p-base text-ink-gray-6">{{ post.excerpt || excerpt(post.content, 140) }}</p>
                </div>
                <div class="mt-2 text-xs text-ink-gray-5">
                  {{ formatDate(post.creation) }} · {{ readTime(post.content) }} min read ·
                  {{ post.comment_count }} comment{{ post.comment_count === 1 ? '' : 's' }}
                </div>
              </div>
              <img
                v-if="thumbnailFor(post)"
                :src="thumbnailFor(post)"
                loading="lazy"
                decoding="async"
                class="h-20 w-24 shrink-0 rounded-md object-cover"
              />
            </router-link>
          </div>
          <p v-else class="mt-6 text-base text-ink-gray-5">No posts yet.</p>
        </template>
      </template>
    </div>
  </ScrollArea>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Breadcrumbs,
  Button,
  LoadingText,
  PageHeader,
  PageHeaderBackButton,
  PageHeaderMobile,
  ScrollArea,
  Tabs,
  useCall,
  useList,
} from 'frappe-ui'
import { session } from '@/data/session'
import { APP_NAME } from '@/utils/appName'
import MobileNotificationBell from '@/components/MobileNotificationBell.vue'
import { useIsMobile } from '@/composables/useIsMobile'

const isMobile = useIsMobile()

const route = useRoute()
const router = useRouter()
const targetUser = computed(() => route.params.userId || session.user)
const isOwnProfile = computed(() => targetUser.value === session.user)

const profile = useCall({
  url: '/api/v2/method/my_new_app.api.get_profile',
  params: () => ({ user: targetUser.value }),
})

// limit: 0 means "no limit" server-side (see Profile.vue's own posts list for
// the same convention) - this page's whole point is showing all of them.
const posts = useCall({
  url: '/api/v2/method/my_new_app.api.list_profile_posts',
  params: () => ({ user: targetUser.value, limit: 0 }),
  refetch: true,
})

const ownTabs = [{ label: 'Published' }, { label: 'Drafts' }, { label: 'Archived' }]

// Same URL-query persistence as Settings.vue's own tabs, and for the same
// reason: clicking into a post (or the editor) navigates away and destroys
// this component, so a plain local ref would always reset to "Published"
// when the browser's back button returns here.
function tabIndexFromQuery() {
  const idx = ownTabs.findIndex((t) => t.label.toLowerCase() === route.query.tab)
  return idx === -1 ? 0 : idx
}
const tab = ref(tabIndexFromQuery())
watch(tab, (idx) => {
  const slug = idx === 0 ? undefined : ownTabs[idx].label.toLowerCase()
  if ((route.query.tab || undefined) === slug) return
  const query = { ...route.query }
  if (slug) query.tab = slug
  else delete query.tab
  router.replace({ query })
})

const draftArchiveFilters = computed(() => ({
  author: targetUser.value,
  status: ownTabs[tab.value]?.label === 'Drafts' ? 'Draft' : 'Archived',
}))

const draftArchivePosts = useList({
  doctype: 'Post',
  fields: ['name', 'title', 'display_title', 'content', 'excerpt', 'status', 'modified', 'post_type', 'cover_image', 'attachment'],
  filters: draftArchiveFilters,
  orderBy: 'modified desc',
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

// Same own-vs-other-profile pattern as Profile.vue's breadcrumbs, with a
// trailing "Posts" crumb - own profile's "Profile" crumb becomes a link back
// now that this page sits one level deeper than it.
const breadcrumbItems = computed(() => {
  if (isOwnProfile.value) {
    return [{ label: APP_NAME, route: '/' }, { label: 'Profile', route: '/profile' }, { label: 'Posts' }]
  }
  return [
    { label: APP_NAME, route: '/' },
    { label: 'Explore', route: '/' },
    { label: profile.data?.full_name || 'Profile', route: `/profile/${targetUser.value}` },
    { label: 'Posts' },
  ]
})
</script>

<style scoped>
/* Same tablist spacing fix as Settings.vue's tabs - see that file's comment
   for the exact rationale (zeroing the tablist's own padding so tab labels
   align with this page's content rows below, widening the gap to match). */
.posts-tabs :deep([role='tablist']) {
  padding: 0;
  gap: 32px;
}
.posts-tabs :deep([role='tab']) {
  padding-top: 8px;
  padding-bottom: 8px;
}
</style>
