<template>
  <SettingsDialog v-model="open" v-model:tab="settingsTab">
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
        <SettingsHeader title="Account" class="pb-5" />
        <SettingsBody><AccountSettings /></SettingsBody>
      </SettingsPanel>
      <SettingsPanel value="saved">
        <SettingsHeader title="Saved posts" class="pb-5" />
        <SettingsBody><SavedPostsSettings @navigate="open = false" /></SettingsBody>
      </SettingsPanel>
    </SettingsContent>
  </SettingsDialog>
</template>

<script setup>
import { computed } from 'vue'
import {
  Avatar,
  SettingsBody,
  SettingsContent,
  SettingsDialog,
  SettingsHeader,
  SettingsNavGroup,
  SettingsNavItem,
  SettingsPanel,
  SettingsSidebar,
} from 'frappe-ui'
import { session } from '@/data/session'
import { settingsTab } from '@/data/settings'
import AccountSettings from './AccountSettings.vue'
import SavedPostsSettings from './SavedPostsSettings.vue'

const open = defineModel({ type: Boolean, default: false })

const username = computed(() => (session.user || '').split('@')[0])
</script>
