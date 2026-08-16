<template>
  <div class="relative">
    <Button variant="ghost" theme="gray" icon="lucide-bell" @click="notificationsOpen = true" />
    <Badge
      v-if="unreadNotifCount.data"
      variant="solid"
      theme="red"
      size="sm"
      class="pointer-events-none absolute -right-0.5 -top-0.5"
    >
      {{ unreadNotifCount.data }}
    </Badge>
  </div>
</template>

<script setup>
import { Badge, Button } from 'frappe-ui'
import { notificationsOpen, unreadNotifCount } from '@/data/notifications'
</script>
