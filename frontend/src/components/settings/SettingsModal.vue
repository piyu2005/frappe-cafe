<template>
  <SettingsDialog v-model="open" v-model:tab="tab">
    <!-- The dialog is full screen on mobile with no close control of its own. -->
    <Button
      class="absolute right-2 top-2 z-10 sm:hidden"
      variant="ghost"
      icon="lucide-x"
      aria-label="Close settings"
      @click="open = false"
    />
    <SettingsSidebar>
      <SettingsNavGroup label="User settings">
        <SettingsNavItem value="account">
          <template #prefix>
            <Avatar size="xs" :label="username" class="shrink-0" />
          </template>
          Account
        </SettingsNavItem>
        <SettingsNavItem value="saved">
          <template #prefix>
            <span class="lucide-bookmark size-4 shrink-0 text-ink-gray-6" aria-hidden="true" />
          </template>
          Saved posts
        </SettingsNavItem>
      </SettingsNavGroup>
    </SettingsSidebar>

    <SettingsContent>
      <SettingsPanel value="account">
        <AccountSettings />
      </SettingsPanel>
      <SettingsPanel value="saved">
        <SavedPostsSettings @navigate="open = false" />
      </SettingsPanel>
    </SettingsContent>
  </SettingsDialog>
</template>

<script setup>
import { computed, ref } from 'vue'
import {
  Avatar,
  Button,
  SettingsContent,
  SettingsDialog,
  SettingsNavGroup,
  SettingsNavItem,
  SettingsPanel,
  SettingsSidebar,
} from 'frappe-ui'
import { session } from '@/data/session'
import AccountSettings from './AccountSettings.vue'
import SavedPostsSettings from './SavedPostsSettings.vue'

const open = defineModel({ type: Boolean, default: false })
const tab = ref('account')

const username = computed(() => (session.user || '').split('@')[0])
</script>
