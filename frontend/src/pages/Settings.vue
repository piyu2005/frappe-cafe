<template>
  <PageHeader v-if="!isMobile">
    <Breadcrumbs :items="[{ label: APP_NAME, route: '/' }, { label: 'Settings' }]" />
    <Button variant="solid" theme="gray" icon-left="lucide-plus" label="New Post" route="/write" />
  </PageHeader>
  <ScrollArea class="h-full">
    <div class="mx-auto max-w-[760px] px-4 py-6 sm:px-5 sm:py-8">
      <Tabs v-model="tab" :tabs="tabs" class="settings-tabs">
        <template #tab-panel="{ tab: activeTab }">
          <div v-if="activeTab.label === 'Account'" class="divide-y divide-outline-gray-1">
            <div class="flex items-center justify-between py-4">
              <span class="text-base-medium text-ink-gray-8">Username & Subdomain</span>
              <span class="text-sm text-ink-gray-5">@{{ username }}</span>
            </div>
            <div class="flex items-center justify-between py-4">
              <span class="text-base-medium text-ink-gray-8">Email Address</span>
              <span class="text-sm text-ink-gray-5">{{ session.user }}</span>
            </div>
            <div class="flex items-center justify-between py-4">
              <div>
                <div class="text-base-medium text-ink-gray-8">Private account</div>
                <p class="text-sm text-ink-gray-5">
                  When on, people must send a follow request to follow you.
                </p>
              </div>
              <Switch v-model="isPrivate" :disabled="updatePrivacy.loading" @update:model-value="handlePrivacyToggle" />
            </div>
            <button
              class="flex w-full items-center justify-between py-4 text-left"
              @click="openChangePassword"
            >
              <span class="text-base-medium text-ink-gray-8">Change Password</span>
              <span class="lucide-arrow-right size-4 text-ink-gray-5" aria-hidden="true" />
            </button>
            <button
              class="flex w-full items-center justify-between py-4 text-left"
              @click="handleLogout"
            >
              <span class="text-base-medium text-ink-gray-8">Log out</span>
              <span class="lucide-log-out size-4 text-ink-gray-5" aria-hidden="true" />
            </button>
            <button
              class="flex w-full items-center justify-between py-4 text-left"
              @click="confirmDeleteAccount"
            >
              <span class="text-base-medium text-ink-red-6">Delete account</span>
              <span class="lucide-trash-2 size-4 text-ink-red-6" aria-hidden="true" />
            </button>
          </div>

          <div v-else-if="activeTab.label === 'Saved'" class="pt-4">
            <LoadingText v-if="savedPosts.loading && !savedPosts.data" :lines="4" />
            <p
              v-else-if="savedPosts.data && savedPosts.data.length === 0"
              class="text-p-base text-ink-gray-6"
            >
              No saved posts yet.
            </p>
            <div v-else class="divide-y divide-outline-gray-1">
              <div v-for="p in savedPosts.data" :key="p.name" class="flex items-center gap-3 py-4">
                <router-link
                  :to="{ name: 'PostDetail', params: { postId: p.name } }"
                  class="flex min-w-0 flex-1 items-stretch gap-4"
                >
                  <div class="min-w-0 flex-1">
                    <div class="truncate text-base-medium text-ink-gray-9">{{ p.display_title || p.title || 'Untitled' }}</div>
                    <p class="mt-1 line-clamp-2 text-p-sm text-ink-gray-6">{{ excerpt(p.content, 140) }}</p>
                    <div class="mt-1 text-xs text-ink-gray-5">By {{ p.author_name }}</div>
                  </div>
                  <img
                    v-if="coverImageFor(p)"
                    :src="coverImageFor(p)"
                    class="h-20 w-24 shrink-0 rounded-md object-cover"
                  />
                </router-link>
                <Button
                  icon="lucide-bookmark-minus"
                  variant="ghost"
                  :loading="unsavePost.loading"
                  @click="unsave(p.name)"
                />
              </div>
            </div>
          </div>

          <div v-else class="pt-4">
            <LoadingText v-if="draftArchivePosts.loading && !draftArchivePosts.data" :lines="4" />
            <p
              v-else-if="!draftArchivePosts.data || draftArchivePosts.data.length === 0"
              class="text-p-base text-ink-gray-6"
            >
              {{ activeTab.label === 'Drafts' ? "You don't have any drafts." : "You don't have any archived posts." }}
            </p>
            <div v-else class="divide-y divide-outline-gray-1">
              <router-link
                v-for="p in draftArchivePosts.data"
                :key="p.name"
                :to="{ name: 'WritePost', params: { postId: p.name } }"
                class="flex items-stretch justify-between gap-4 py-4"
              >
                <div class="min-w-0 flex-1">
                  <div class="truncate text-base-medium text-ink-gray-9">{{ p.display_title || p.title || 'Untitled' }}</div>
                  <p class="mt-1 line-clamp-2 text-p-sm text-ink-gray-6">{{ excerpt(p.content, 140) }}</p>
                  <div class="mt-1 text-xs text-ink-gray-5">{{ formatDate(p.modified) }}</div>
                </div>
                <img
                  v-if="coverImageFor(p)"
                  :src="coverImageFor(p)"
                  class="h-20 w-24 shrink-0 rounded-md object-cover"
                />
              </router-link>
            </div>
          </div>
        </template>
      </Tabs>
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
  ScrollArea,
  Switch,
  Tabs,
  dialog,
  toast,
  useCall,
  useList,
} from 'frappe-ui'
import { logout, session } from '@/data/session'
import { APP_NAME } from '@/utils/appName'
import { useIsMobile } from '@/composables/useIsMobile'

const isMobile = useIsMobile()

const route = useRoute()
const router = useRouter()

const tabs = [{ label: 'Account' }, { label: 'Saved' }, { label: 'Drafts' }, { label: 'Archived' }]

// Which tab was open lives in the URL (?tab=drafts) rather than plain local
// state — clicking into a post navigates away and destroys this component,
// so a local ref alone would always come back on the default "Account" tab
// when the browser's back button returns here, regardless of which tab was
// actually open. router.replace (not push) so switching tabs doesn't add
// its own back-button stops — only the tab active when you navigate away
// needs to be the one restored.
function tabIndexFromQuery() {
  const idx = tabs.findIndex((t) => t.label.toLowerCase() === route.query.tab)
  return idx === -1 ? 0 : idx
}

const tab = ref(tabIndexFromQuery())

watch(tab, (idx) => {
  const slug = idx === 0 ? undefined : tabs[idx].label.toLowerCase()
  if ((route.query.tab || undefined) === slug) return
  const query = { ...route.query }
  if (slug) query.tab = slug
  else delete query.tab
  router.replace({ query })
})

const username = computed(() => (session.user || '').split('@')[0])
const isPrivate = ref(false)

const profile = useCall({
  url: '/api/v2/method/my_new_app.api.get_profile',
  params: { user: session.user },
  onSuccess: (data) => {
    isPrivate.value = !!data.is_private
  },
})

const updatePrivacy = useCall({
  url: '/api/v2/method/my_new_app.api.update_profile',
  method: 'POST',
  immediate: false,
  onSuccess: () => toast.success(isPrivate.value ? 'Account is now private' : 'Account is now public'),
  onError: (err) => {
    toast.error(err.message)
    isPrivate.value = !isPrivate.value
  },
})

function handlePrivacyToggle(value) {
  updatePrivacy.submit({ is_private: value ? 1 : 0 })
}

const changePassword = useCall({
  url: '/api/v2/method/my_new_app.api.change_password',
  method: 'POST',
  immediate: false,
  onSuccess: () => toast.success('Password updated'),
  onError: (err) => toast.error(err.message),
})

const deleteAccount = useCall({
  url: '/api/v2/method/my_new_app.api.delete_account',
  method: 'POST',
  immediate: false,
  onSuccess: async () => {
    await logout()
    router.replace('/login')
  },
})

function handleLogout() {
  dialog.confirm({
    title: 'Log out?',
    message: 'You can always log back in.',
    confirmLabel: 'Log out',
    onConfirm: async () => {
      await logout()
      router.replace('/login')
    },
  })
}

function openChangePassword() {
  dialog.prompt({
    title: 'Change password',
    fields: [
      { name: 'old_password', label: 'Current password', type: 'password', required: true },
      { name: 'new_password', label: 'New password', type: 'password', required: true },
      {
        name: 'confirm_password',
        label: 'Confirm new password',
        type: 'password',
        required: true,
        validate: (value, allValues) =>
          value !== allValues.new_password ? 'Passwords do not match' : undefined,
      },
    ],
    onConfirm: ({ values, close }) => {
      changePassword.submit({ old_password: values.old_password, new_password: values.new_password })
      close()
    },
  })
}

function confirmDeleteAccount() {
  dialog.confirm({
    title: 'Delete account?',
    message: 'This will disable your account and log you out. This cannot be undone.',
    theme: 'red',
    confirmLabel: 'Delete',
    onConfirm: () => deleteAccount.submit({}),
  })
}

const savedPosts = useCall({
  url: '/api/v2/method/my_new_app.api.list_saved_posts',
})

const unsavePost = useCall({
  url: '/api/v2/method/my_new_app.api.toggle_save_post',
  method: 'POST',
  immediate: false,
  onSuccess: () => savedPosts.reload(),
})

function unsave(postId) {
  unsavePost.submit({ post: postId })
}

const draftArchiveFilters = computed(() => ({
  author: session.user,
  status: tabs[tab.value]?.label === 'Drafts' ? 'Draft' : 'Archived',
}))

const draftArchivePosts = useList({
  doctype: 'Post',
  fields: [
    'name',
    'title',
    'display_title',
    'content',
    'excerpt',
    'status',
    'modified',
    'post_type',
    'cover_image',
    'attachment',
  ],
  filters: draftArchiveFilters,
  orderBy: 'modified desc',
  refetch: true,
})

function coverImageFor(post) {
  if (post.cover_image) return post.cover_image
  if (post.post_type !== 'Video') return post.attachment
  return null
}

function formatDate(value) {
  if (!value) return ''
  return new Date(value).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
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
</script>

<style scoped>
/* Tabs' own tablist carries a built-in horizontal px-5, on top of this
   page's container padding — so the tab labels sat further right than the
   content rows below them, which have no padding of their own. Zeroing just
   the tablist's left/right padding lines them back up. */
.settings-tabs :deep([role='tablist']) {
  padding-left: 0;
  padding-right: 0;
}
</style>
