<template>
  <div class="divide-y divide-outline-gray-1">
    <SettingsRow title="Username">
      <span class="text-base text-ink-gray-6">@{{ username }}</span>
    </SettingsRow>
    <SettingsRow title="Email address">
      <span class="text-base text-ink-gray-6">{{ session.user }}</span>
    </SettingsRow>
    <SettingsRow title="Log out" description="Sign out of your account on this device.">
      <Button label="Log out" @click="confirmLogout" />
    </SettingsRow>
    <SettingsRow
      title="Delete account"
      description="Temporarily unavailable. Contact support if you need this."
    >
      <Button label="Delete account" theme="red" disabled />
    </SettingsRow>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { Button, SettingsRow, dialog } from 'frappe-ui'
import { logout, session } from '@/data/session'

const router = useRouter()
const username = computed(() => (session.user || '').split('@')[0])

function confirmLogout() {
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
</script>
