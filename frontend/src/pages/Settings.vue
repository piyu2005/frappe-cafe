<template>
  <PageHeader v-if="!isMobile">
    <Breadcrumbs :items="[{ label: APP_NAME, route: '/' }, { label: 'Settings' }]" />
    <Button variant="solid" theme="gray" icon-left="lucide-plus" label="New Post" route="/write" />
  </PageHeader>
  <PageHeaderMobile v-else title="Settings">
    <template #right>
      <Button variant="solid" theme="gray" icon="lucide-plus" route="/write" />
    </template>
  </PageHeaderMobile>

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

          <div v-else class="pt-4">
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
                  class="block min-w-0 flex-1"
                >
                  <div class="truncate text-base-medium text-ink-gray-9">{{ p.display_title || p.title || 'Untitled' }}</div>
                  <p class="mt-1 line-clamp-2 text-p-sm text-ink-gray-6">{{ excerpt(p.content, 140) }}</p>
                  <div class="mt-1 text-xs text-ink-gray-5">By {{ p.author_name }}</div>
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
        </template>
      </Tabs>
    </div>
  </ScrollArea>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  Breadcrumbs,
  Button,
  LoadingText,
  PageHeader,
  PageHeaderMobile,
  ScrollArea,
  Switch,
  Tabs,
  dialog,
  toast,
  useCall,
} from 'frappe-ui'
import { logout, session } from '@/data/session'
import { APP_NAME } from '@/utils/appName'
import { useIsMobile } from '@/composables/useIsMobile'

const isMobile = useIsMobile()

const router = useRouter()

const tab = ref(0)
const tabs = [{ label: 'Account' }, { label: 'Saved' }]

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
