<template>
  <div class="h-screen w-screen overflow-hidden bg-surface-base text-ink-gray-9">
    <MobileShell v-if="isMobile">
      <router-view />
      <template #nav>
        <MobileNav>
          <MobileNavItem
            label="Home"
            icon="lucide-house"
            :active="!notificationsOpen && route.name === 'Home'"
            :to="{ name: 'Home' }"
            @click="notificationsOpen = false"
          />
          <MobileNavItem
            label="Explore"
            icon="lucide-search"
            :active="!notificationsOpen && route.name === 'SearchPeople'"
            :to="{ name: 'SearchPeople' }"
            @click="notificationsOpen = false"
          />
          <MobileNavItem
            label="Messages"
            icon="lucide-message-circle"
            :active="!notificationsOpen && route.name === 'Messages'"
            :to="{ name: 'Messages' }"
            @click="notificationsOpen = false"
          >
            <template #default="{ active }">
              <span class="relative">
                <span
                  class="lucide-message-circle size-6"
                  :class="active ? 'text-ink-gray-8' : 'text-ink-gray-5'"
                  aria-hidden="true"
                />
                <Badge
                  v-if="unreadMessageCount.data"
                  variant="solid"
                  theme="red"
                  size="sm"
                  class="absolute -right-2 -top-1.5"
                >
                  {{ unreadMessageCount.data }}
                </Badge>
              </span>
            </template>
          </MobileNavItem>
          <MobileNavItem
            label="Profile"
            icon="lucide-user"
            :active="!notificationsOpen && route.name === 'Profile'"
            :to="{ name: 'Profile' }"
            @click="notificationsOpen = false"
          />
          <MobileNavItem
            label="Settings"
            icon="lucide-settings"
            :active="!notificationsOpen && route.name === 'Settings'"
            :to="{ name: 'Settings' }"
            @click="notificationsOpen = false"
          />
        </MobileNav>
      </template>
    </MobileShell>

    <DesktopShell v-else>
      <template v-if="!sidebarOpen" #rail>
        <Rail class="border-r border-outline-gray-1">
          <div class="flex w-full flex-col items-center gap-3">
            <button
              type="button"
              class="flex h-9 w-9 items-center justify-center rounded-xl bg-surface-gray-10"
              @click="sidebarOpen = true"
            >
              <span class="lucide-feather size-4 text-ink-base" aria-hidden="true" />
            </button>

            <RailItem
              label="Home"
              variant="ghost"
              icon="lucide-house"
              :active="!notificationsOpen && route.name === 'Home'"
              to="/"
              @click="(e) => { notificationsOpen = false; blurTrigger(e) }"
            />
            <RailItem
              label="Search"
              variant="ghost"
              icon="lucide-search"
              :active="!notificationsOpen && route.name === 'SearchPeople'"
              :to="{ name: 'SearchPeople' }"
              @click="(e) => { notificationsOpen = false; blurTrigger(e) }"
            />
            <RailItem
              label="Messages"
              variant="ghost"
              icon="lucide-message-circle"
              :active="!notificationsOpen && route.name === 'Messages'"
              :badge="unreadMessageCount.data || 0"
              badge-style="count"
              :to="{ name: 'Messages' }"
              @click="(e) => { notificationsOpen = false; blurTrigger(e) }"
            />
            <RailItem
              label="Notifications"
              variant="ghost"
              icon="lucide-bell"
              :active="notificationsOpen"
              :badge="unreadNotifCount.data || 0"
              badge-style="count"
              @click="(e) => { notificationsOpen = !notificationsOpen; blurTrigger(e) }"
            />
            <RailItem
              label="Profile"
              variant="ghost"
              icon="lucide-user"
              :active="!notificationsOpen && route.name === 'Profile'"
              :to="{ name: 'Profile' }"
              @click="(e) => { notificationsOpen = false; blurTrigger(e) }"
            />
            <RailItem
              label="Settings"
              variant="ghost"
              icon="lucide-settings"
              :active="!notificationsOpen && route.name === 'Settings'"
              :to="{ name: 'Settings' }"
              @click="(e) => { notificationsOpen = false; blurTrigger(e) }"
            />
          </div>

          <!-- Mirrors frappe-ui's own SidebarCollapseToggle (same icon,
               rotation, and transition) so expanding from the rail uses the
               exact same affordance real Frappe products use for the
               opposite direction — see the matching Sidebar-side toggle
               below. Kept separate from the logo button above (which still
               expands on click too) since that's branding, not a labeled
               collapse/expand control. -->
          <div class="mt-auto flex w-full flex-col items-center gap-3">
            <RailItem label="Expand" variant="ghost" @click="(e) => { sidebarOpen = true; blurTrigger(e) }">
              <span
                class="lucide-panel-right-open size-4 rotate-180 transition-transform duration-300 ease-in-out"
                aria-hidden="true"
              />
            </RailItem>
          </div>
        </Rail>
      </template>

      <template v-else #sidebar>
        <Sidebar disable-collapse width="14rem" class="border-r border-outline-gray-1">
          <!-- App switcher header — matches frappe-ui's own Sidebar composition
               convention (p-2 wrapper, h-8 full-width button, size-6 mark). -->
          <div class="flex shrink-0 items-center p-2.5">
            <button
              type="button"
              class="flex h-9 w-full items-center gap-2 rounded px-1 transition hover:bg-surface-gray-2"
              @click="sidebarOpen = false"
            >
              <div class="grid size-9 shrink-0 place-items-center rounded-xl bg-surface-gray-10 text-ink-base">
                <span class="lucide-feather size-4" aria-hidden="true" />
              </div>
              <span class="flex-1 truncate text-left text-base text-ink-gray-8">{{ APP_NAME }}</span>
            </button>
          </div>

          <nav class="mt-0.5 space-y-3 px-2">
            <SidebarItem
              label="Feed"
              icon="lucide-house"
              :active="!notificationsOpen && route.name === 'Home'"
              to="/"
              @click="notificationsOpen = false"
            />
            <SidebarItem
              label="Explore"
              icon="lucide-search"
              :active="!notificationsOpen && route.name === 'SearchPeople'"
              :to="{ name: 'SearchPeople' }"
              @click="notificationsOpen = false"
            />
            <SidebarItem
              label="Messages"
              icon="lucide-message-circle"
              :active="!notificationsOpen && route.name === 'Messages'"
              :to="{ name: 'Messages' }"
              @click="notificationsOpen = false"
            >
              <template v-if="unreadMessageCount.data" #suffix>
                <div class="relative mr-1 flex size-7 shrink-0 items-center justify-end">
                  <Badge variant="solid" theme="red" size="sm">{{ unreadMessageCount.data }}</Badge>
                </div>
              </template>
            </SidebarItem>
            <SidebarItem
              label="Notifications"
              icon="lucide-bell"
              :active="notificationsOpen"
              @click="notificationsOpen = !notificationsOpen"
            >
              <template v-if="unreadNotifCount.data" #suffix>
                <div class="relative mr-1 flex size-7 shrink-0 items-center justify-end">
                  <Badge variant="solid" theme="red" size="sm">{{ unreadNotifCount.data }}</Badge>
                </div>
              </template>
            </SidebarItem>
            <SidebarItem
              label="Profile"
              icon="lucide-user"
              :active="!notificationsOpen && route.name === 'Profile'"
              :to="{ name: 'Profile' }"
              @click="notificationsOpen = false"
            />
            <SidebarItem
              label="Settings"
              icon="lucide-settings"
              :active="!notificationsOpen && route.name === 'Settings'"
              :to="{ name: 'Settings' }"
              @click="notificationsOpen = false"
            />
          </nav>

          <!-- Same icon/rotation as frappe-ui's own SidebarCollapseToggle
               (used verbatim on the rail side above) — reimplemented as a
               plain SidebarItem here rather than that component directly,
               since it toggles our own Rail/Sidebar swap (`sidebarOpen`)
               rather than frappe-ui Sidebar's own internal collapsed state,
               which this app opts out of via `disable-collapse` in favor of
               swapping to a distinct icon-only Rail. -->
          <div class="mt-auto px-2 pb-2">
            <SidebarItem label="Collapse" @click="sidebarOpen = false">
              <template #prefix>
                <span
                  class="lucide-panel-right-open size-4 text-ink-gray-6 transition-transform duration-300 ease-in-out"
                  aria-hidden="true"
                />
              </template>
            </SidebarItem>
          </div>
        </Sidebar>
      </template>

      <router-view />
    </DesktopShell>

    <NotificationsPanel v-model="notificationsOpen" :rail-offset="railOffset" :full-screen="isMobile" />
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import {
  Badge,
  DesktopShell,
  MobileNav,
  MobileNavItem,
  MobileShell,
  Rail,
  RailItem,
  Sidebar,
  SidebarItem,
  toast,
} from 'frappe-ui'
import { getSocket } from '@/data/socket'
import { notificationsOpen, unreadNotifCount } from '@/data/notifications'
import { unreadMessageCount } from '@/data/messages'
import { useIsMobile } from '@/composables/useIsMobile'
import { APP_NAME } from '@/utils/appName'
import NotificationsPanel from './NotificationsPanel.vue'

const route = useRoute()
const isMobile = useIsMobile()
const sidebarOpen = ref(false)
// Matches the rail's fixed w-[50px] and the sidebar's explicit width prop
// below, so the panel sits next to whichever is currently showing instead of
// covering it.
const railOffset = computed(() => (sidebarOpen.value ? '14rem' : '50px'))

// Navigating away (Home, Search, Messages, a profile link, ...) should close
// the notifications panel rather than leaving it hanging open over whatever
// page you just switched to.
watch(
  () => route.fullPath,
  () => {
    notificationsOpen.value = false
  },
)

// RailItem's Tooltip (unlike SidebarItem's) has no way to disable itself, and
// reka-ui opens tooltips on focus as well as hover for keyboard accessibility.
// A mouse click still leaves the trigger focused afterwards, so without this
// its tooltip can pop back open later with no real hover behind it — e.g.
// after the panel/route changes and reflows, or focus otherwise returns near
// the rail. Blurring right after the click removes that lingering focus so
// the tooltip only ever shows for an actual hover or deliberate Tab press.
function blurTrigger(event) {
  event.currentTarget?.blur()
}

function handleNewMessage(payload) {
  unreadMessageCount.reload()
  if (route.name !== 'Messages' || route.params.conversationId !== payload.conversation) {
    toast.info(`${payload.sender_name}: ${payload.content || 'sent an attachment'}`)
  }
}

function handleNewNotification(payload) {
  unreadNotifCount.reload()
  if (!notificationsOpen.value) {
    toast.info(`${payload.actor_name || 'Someone'} ${payload.message}`)
  }
}

let socket = null
onMounted(() => {
  socket = getSocket()
  socket.on('chat:new_message', handleNewMessage)
  socket.on('notification:new', handleNewNotification)
})

onBeforeUnmount(() => {
  if (socket) {
    socket.off('chat:new_message', handleNewMessage)
    socket.off('notification:new', handleNewNotification)
  }
})
</script>

<style scoped>
/* Icon-only bottom nav on mobile — MobileNavItem has no prop to omit its
   label (only "under the icon"), so hide it visually here while leaving the
   label prop itself (and the aria-label it drives) untouched, keeping the
   bar accessible to screen readers even without the visible text. Scoped to
   `[data-slot="mobile-nav"]` specifically, so it can't ever reach the
   desktop rail/sidebar's own labels. */
:deep([data-slot='mobile-nav'] .text-xs-medium) {
  display: none;
}
</style>
