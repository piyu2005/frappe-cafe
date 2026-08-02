<template>
  <div class="h-screen w-screen overflow-hidden bg-surface-base text-ink-gray-9">
    <DesktopShell>
      <template #rail>
        <Rail class="border-r border-outline-gray-1">
          <div class="flex w-full flex-col items-center gap-3 pt-3">
            <router-link
              to="/"
              class="flex h-9 w-9 items-center justify-center rounded-xl bg-surface-gray-10"
            >
              <span class="lucide-feather size-4 text-ink-base" aria-hidden="true" />
            </router-link>

            <RailItem
              label="Home"
              variant="ghost"
              icon="lucide-house"
              :active="route.name === 'Home'"
              to="/"
            />
            <RailItem
              label="Search"
              variant="ghost"
              icon="lucide-search"
              :active="route.name === 'SearchPeople'"
              :to="{ name: 'SearchPeople' }"
            />
            <RailItem
              label="Messages"
              variant="ghost"
              icon="lucide-message-circle"
              :active="route.name === 'Messages'"
              :badge="unreadMessageCount.data || 0"
              badge-style="count"
              :to="{ name: 'Messages' }"
            />
            <RailItem
              label="Notifications"
              variant="ghost"
              icon="lucide-bell"
              :active="route.name === 'Notifications'"
              :badge="unreadNotifCount.data || 0"
              badge-style="count"
              :to="{ name: 'Notifications' }"
            />
            <RailItem
              label="Profile"
              variant="ghost"
              :active="route.name === 'Profile'"
              :to="{ name: 'Profile' }"
            >
              <Avatar :image="myProfile.data?.user_image" :label="myProfile.data?.full_name || session.user" size="md" />
            </RailItem>
            <RailItem
              label="Settings"
              variant="ghost"
              icon="lucide-settings"
              :active="route.name === 'Settings'"
              :to="{ name: 'Settings' }"
            />
          </div>
        </Rail>
      </template>

      <router-view />
    </DesktopShell>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { Avatar, DesktopShell, Rail, RailItem, toast, useCall } from 'frappe-ui'
import { session } from '@/data/session'
import { getSocket } from '@/data/socket'
import { unreadNotifCount } from '@/data/notifications'
import { unreadMessageCount } from '@/data/messages'

const route = useRoute()

const myProfile = useCall({
  url: '/api/v2/method/my_new_app.api.get_profile',
})

function handleNewMessage(payload) {
  unreadMessageCount.reload()
  if (route.name !== 'Messages' || route.params.conversationId !== payload.conversation) {
    toast.info(`${payload.sender_name}: ${payload.content || 'sent an attachment'}`)
  }
}

function handleNewNotification(payload) {
  unreadNotifCount.reload()
  if (route.name !== 'Notifications') {
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
