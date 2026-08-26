<template>
  <Teleport to="body">
    <!--
      No backdrop — this panel sits alongside the app, not on top of it: the
      rest of the page stays fully clickable/scrollable while it's open.
      Dismiss via the X button or clicking the bell again (toggled in
      AppLayout), not a click-outside catcher.
    -->
    <!--
      Same fade the nav items themselves use for their active-state highlight
      (frappe-ui's bare `transition` utility — all-property, 150ms, default
      ease) rather than a slide — that's the "barely-there" motion already
      established everywhere else you select something from the sidebar/rail.
    -->
    <Transition
      enter-active-class="transition"
      leave-active-class="transition"
      enter-from-class="opacity-0"
      leave-to-class="opacity-0"
    >
      <div
        v-if="open"
        class="fixed inset-y-0 z-50 flex flex-col bg-surface-base"
        :class="
          fullScreen
            ? 'inset-x-0 w-full'
            : 'w-80 max-w-[90vw] border-r border-outline-gray-1 shadow-[8px_0_15px_-3px_rgba(0,0,0,0.1),4px_0_6px_-4px_rgba(0,0,0,0.1)]'
        "
        :style="fullScreen ? {} : { left: railOffset }"
      >
        <div class="flex min-h-12 shrink-0 items-center justify-between border-b border-outline-gray-1 px-4">
          <h2 class="text-lg-semibold text-ink-gray-9">Notifications</h2>
          <div class="flex items-center gap-1">
            <Button
              variant="ghost"
              label="Mark all as read"
              size="sm"
              :loading="markAllRead.loading"
              @click="markAllRead.submit({})"
            />
            <button
              type="button"
              class="flex size-7 items-center justify-center rounded text-ink-gray-5 hover:bg-surface-gray-2 hover:text-ink-gray-8"
              @click="open = false"
            >
              <span class="lucide-x size-4" aria-hidden="true" />
            </button>
          </div>
        </div>

        <ScrollArea class="min-h-0 flex-1">
          <LoadingText v-if="notifications.loading && !notifications.data" class="p-4" :lines="6" />

          <div
            v-else-if="notifications.data && notifications.data.length === 0"
            class="flex flex-col items-center gap-3 px-4 py-24 text-center"
          >
            <span class="lucide-bell size-8 text-ink-gray-3" aria-hidden="true" />
            <p class="text-p-base text-ink-gray-5">You're all caught up.</p>
          </div>

          <div v-else class="divide-y divide-outline-gray-1">
            <div
              v-for="n in notifications.data"
              :key="n.name"
              class="flex cursor-pointer items-start gap-3 px-3 py-3 hover:bg-surface-gray-1"
              @click="handleClick(n)"
            >
              <div class="relative shrink-0">
                <Avatar :image="n.actor_image" :label="n.actor_name || 'Someone'" size="md" />
                <span
                  class="absolute -bottom-1 -right-1 flex size-3.5 items-center justify-center rounded-full"
                  :class="iconBgFor(n.type)"
                >
                  <span :class="iconFor(n.type)" class="size-2 text-white" aria-hidden="true" />
                </span>
              </div>

              <div class="min-w-0 flex-1">
                <p class="text-p-sm" :class="n.is_read ? 'text-ink-gray-7' : 'text-ink-gray-9'">
                  <span class="text-sm-medium text-ink-gray-9">{{ n.actor_name || 'Someone' }}</span>
                  {{ n.message }}
                </p>
                <div class="mt-0.5 text-xs text-ink-gray-5">{{ timeAgo(n.creation) }}</div>

                <div
                  v-if="isRespondable(n.type) && n.request_status === 'Pending'"
                  class="mt-2 flex items-center gap-2"
                >
                  <Button
                    variant="solid"
                    theme="gray"
                    size="sm"
                    label="Accept"
                    :loading="isLoadingKey(n, 'accept')"
                    @click.stop="accept(n)"
                  />
                  <Button
                    variant="outline"
                    theme="gray"
                    size="sm"
                    label="Decline"
                    :loading="isLoadingKey(n, 'decline')"
                    @click.stop="decline(n)"
                  />
                </div>
                <Badge
                  v-else-if="isRespondable(n.type) && n.request_status"
                  class="mt-2"
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
        </ScrollArea>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed, reactive, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Avatar, Badge, Button, LoadingText, ScrollArea, useCall } from 'frappe-ui'
import { unreadNotifCount } from '@/data/notifications'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  // Left offset so the panel sits next to the rail/sidebar instead of
  // covering it — passed down from AppLayout, which is the only place that
  // knows whether the rail or the full sidebar is currently showing.
  railOffset: { type: String, default: '50px' },
  // Mobile has no rail/sidebar to sit alongside — the panel takes the whole
  // screen instead, like any other mobile notification tray.
  fullScreen: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue'])

const open = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

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

// Opening the panel is itself "seeing" what's in it — same as every other
// notification tray (Twitter, LinkedIn, ...). Without this, the unread dots
// only ever cleared by clicking "Mark all as read" or opening each
// notification one at a time, so closing and reopening kept showing the
// same dots even though you'd already looked at them.
watch(open, (isOpen) => {
  if (isOpen) markAllRead.submit({})
})

const respondFollow = useCall({
  url: '/api/v2/method/my_new_app.follow.respond_to_follow_request',
  method: 'POST',
  immediate: false,
  onSuccess: () => notifications.reload(),
})

const respondGroupInvite = useCall({
  url: '/api/v2/method/my_new_app.chat.respond_to_group_invite',
  method: 'POST',
  immediate: false,
  onSuccess: () => notifications.reload(),
})

const respondPublicationInvite = useCall({
  url: '/api/v2/method/my_new_app.api.respond_to_publication_invite',
  method: 'POST',
  immediate: false,
  onSuccess: () => notifications.reload(),
})

// All three request types share the exact same pending/accept/decline shape
// — dispatch to whichever endpoint actually owns this notification's type.
const RESPOND_CALLS = {
  'Follow Request': respondFollow,
  'Group Invite': respondGroupInvite,
  'Publication Invite': respondPublicationInvite,
}

function isRespondable(type) {
  return type in RESPOND_CALLS
}

// Keyed by `${notification name}:accept` / `:decline` — a shared per-*type*
// loading flag (the useCall instance's own `.loading`) would light up both
// buttons on every notification of that type the instant any one of them
// was clicked, since Accept and Decline for every "Group Invite" (say) all
// read the exact same flag. Tracking which specific button on which
// specific notification is in flight keeps the spinner on only the one
// actually clicked.
const loadingKeys = reactive(new Set())

function isLoadingKey(n, action) {
  return loadingKeys.has(`${n.name}:${action}`)
}

// Navigating off *this click's own* resolved promise — not the shared
// useCall's onSuccess/data — matters when two invites are accepted in quick
// succession (e.g. two pending group invites): onSuccess fires against
// whatever `data` the reactive call object currently holds, which is
// whichever response landed most recently, not necessarily the one from
// this particular click. That's exactly how accepting invite A could
// silently drop you into invite B's conversation if B's response happened
// to arrive first. Each `.submit()` call returns its own promise resolved
// with its own response, so chaining off that instead ties the navigation
// to this specific request, regardless of what else is in flight.
function respond(n, action) {
  const call = RESPOND_CALLS[n.type]
  if (!call) return
  const key = `${n.name}:${action}`
  loadingKeys.add(key)
  call
    .submit({ name: n.reference_name, accept: action === 'accept' ? 1 : 0 })
    .then((data) => {
      if (action !== 'accept' || !data) return
      if (data.conversation) {
        open.value = false
        router.push({ name: 'Messages', params: { conversationId: data.conversation } })
      } else if (data.publication) {
        open.value = false
        router.push({ name: 'PublicationDetail', params: { handle: data.publication } })
      }
    })
    .finally(() => loadingKeys.delete(key))
}

function accept(n) {
  respond(n, 'accept')
}

function decline(n) {
  respond(n, 'decline')
}

const ICONS = {
  Like: 'lucide-heart',
  Comment: 'lucide-message-circle',
  'New Post': 'lucide-pen-line',
  'New Follower': 'lucide-user-plus',
  'Follow Request': 'lucide-user-plus',
  'Follow Accepted': 'lucide-user-check',
  Mention: 'lucide-at-sign',
  'Group Invite': 'lucide-users',
  'Publication Invite': 'lucide-newspaper',
}

function iconFor(type) {
  return ICONS[type] || 'lucide-bell'
}

// Color encodes notification type here — deliberate, not decorative (the
// badge is meaningless without it: it's the only thing distinguishing a
// like from a comment from a follow at a glance).
const ICON_BG = {
  Like: 'bg-surface-red-6',
  Comment: 'bg-surface-blue-6',
  'New Post': 'bg-surface-violet-6',
  'New Follower': 'bg-surface-green-6',
  'Follow Request': 'bg-surface-amber-6',
  'Follow Accepted': 'bg-surface-green-6',
  Mention: 'bg-surface-cyan-6',
  'Group Invite': 'bg-surface-amber-6',
  'Publication Invite': 'bg-surface-violet-6',
}

function iconBgFor(type) {
  return ICON_BG[type] || 'bg-surface-gray-8'
}

function notificationRoute(n) {
  if (n.reference_doctype === 'Post') {
    return { name: 'PostDetail', params: { postId: n.reference_name } }
  }
  if (n.reference_doctype === 'Conversation') {
    return { name: 'Messages', params: { conversationId: n.reference_name } }
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
  if (route) {
    open.value = false
    router.push(route)
  }
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
