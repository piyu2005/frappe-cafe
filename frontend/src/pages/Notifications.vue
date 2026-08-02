<template>
  <PageHeader>
    <Breadcrumbs :items="[{ label: APP_NAME, route: '/' }, { label: 'Notifications' }]" />
    <Button
      variant="ghost"
      label="Mark all as read"
      :loading="markAllRead.loading"
      @click="markAllRead.submit({})"
    />
  </PageHeader>

  <ScrollArea class="h-[calc(100vh-3rem)]">
    <div class="mx-auto max-w-[640px] px-5 py-8">
      <LoadingText v-if="notifications.loading && !notifications.data" :lines="6" />

      <div
        v-else-if="notifications.data && notifications.data.length === 0"
        class="flex flex-col items-center gap-3 py-24 text-center"
      >
        <span class="lucide-bell size-8 text-ink-gray-3" aria-hidden="true" />
        <p class="text-p-base text-ink-gray-5">You're all caught up.</p>
      </div>

      <div v-else class="overflow-hidden rounded-md border border-outline-gray-1">
        <div class="divide-y divide-outline-gray-1">
          <div
            v-for="n in notifications.data"
            :key="n.name"
            class="flex cursor-pointer items-start gap-3 p-4 hover:bg-surface-gray-1"
            @click="handleClick(n)"
          >
            <div class="relative shrink-0">
              <Avatar :image="n.actor_image" :label="n.actor_name || 'Someone'" size="xl" />
              <span
                class="absolute -bottom-1 -right-1 flex size-5 items-center justify-center rounded-full ring-2 ring-surface-base"
                :class="iconBgFor(n.type)"
              >
                <span :class="iconFor(n.type)" class="size-3 text-white" aria-hidden="true" />
              </span>
            </div>

            <div class="min-w-0 flex-1">
              <p class="text-p-sm" :class="n.is_read ? 'text-ink-gray-7' : 'text-ink-gray-9'">
                <span class="text-sm-medium text-ink-gray-9">{{ n.actor_name || 'Someone' }}</span>
                {{ n.message }}
              </p>
              <div class="mt-0.5 text-xs text-ink-gray-5">{{ timeAgo(n.creation) }}</div>

              <div
                v-if="n.type === 'Follow Request' && n.request_status === 'Pending'"
                class="mt-2.5 flex items-center gap-2"
              >
                <Button
                  variant="solid"
                  theme="gray"
                  label="Accept"
                  :loading="respond.loading"
                  @click.stop="accept(n)"
                />
                <Button
                  variant="outline"
                  theme="gray"
                  label="Decline"
                  :loading="respond.loading"
                  @click.stop="decline(n)"
                />
              </div>
              <Badge
                v-else-if="n.type === 'Follow Request'"
                class="mt-2.5"
                variant="subtle"
                theme="gray"
                :label="n.request_status"
              />
            </div>

            <span
              v-if="!n.is_read"
              class="mt-2 size-2 shrink-0 rounded-full bg-surface-gray-9"
              aria-hidden="true"
            />
          </div>
        </div>
      </div>
    </div>
  </ScrollArea>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { Avatar, Badge, Breadcrumbs, Button, LoadingText, PageHeader, ScrollArea, useCall } from 'frappe-ui'
import { unreadNotifCount } from '@/data/notifications'
import { APP_NAME } from '@/utils/appName'

const router = useRouter()

const notifications = useCall({
  url: '/api/v2/method/my_new_app.follow.list_notifications',
  refetch: true,
})

const markRead = useCall({
  url: '/api/v2/method/my_new_app.follow.mark_notification_read',
  method: 'POST',
  immediate: false,
  onSuccess: () => unreadNotifCount.reload(),
})

const markAllRead = useCall({
  url: '/api/v2/method/my_new_app.follow.mark_notification_read',
  method: 'POST',
  immediate: false,
  onSuccess: () => {
    notifications.reload()
    unreadNotifCount.reload()
  },
})

const respond = useCall({
  url: '/api/v2/method/my_new_app.follow.respond_to_follow_request',
  method: 'POST',
  immediate: false,
  onSuccess: () => notifications.reload(),
})

function accept(n) {
  respond.submit({ name: n.reference_name, accept: 1 })
}

function decline(n) {
  respond.submit({ name: n.reference_name, accept: 0 })
}

const ICONS = {
  Like: 'lucide-heart',
  Comment: 'lucide-message-circle',
  'New Post': 'lucide-pen-line',
  'New Follower': 'lucide-user-plus',
  'Follow Request': 'lucide-user-plus',
  'Follow Accepted': 'lucide-user-check',
}

function iconFor(type) {
  return ICONS[type] || 'lucide-bell'
}

function iconBgFor() {
  return 'bg-surface-gray-8'
}

function notificationRoute(n) {
  if (n.reference_doctype === 'Post') {
    return { name: 'PostDetail', params: { postId: n.reference_name } }
  }
  if (n.actor) {
    return { name: 'Profile', params: { userId: n.actor } }
  }
  return null
}

function handleClick(n) {
  if (!n.is_read) {
    n.is_read = 1
    markRead.submit({ name: n.name })
  }
  const route = notificationRoute(n)
  if (route) router.push(route)
}

function timeAgo(value) {
  if (!value) return ''
  const seconds = Math.floor((Date.now() - new Date(value)) / 1000)
  const units = [
    ['year', 31536000],
    ['month', 2592000],
    ['day', 86400],
    ['hour', 3600],
    ['minute', 60],
  ]
  for (const [label, secs] of units) {
    const val = Math.floor(seconds / secs)
    if (val >= 1) return `${val} ${label}${val > 1 ? 's' : ''} ago`
  }
  return 'just now'
}
</script>
