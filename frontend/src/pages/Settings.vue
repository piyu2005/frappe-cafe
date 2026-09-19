<template>
  <ScrollArea class="h-full">
    <div class="mx-auto max-w-[600px] px-4 py-6">
      <Tabs v-model="tab" :tabs="tabs" class="settings-tabs">
        <template #tab-panel="{ tab: activeTab }">
          <div class="pt-4">
            <AccountSettings v-if="activeTab.label === 'Account'" />
            <SavedPostsSettings v-else />
          </div>
        </template>
      </Tabs>
    </div>
  </ScrollArea>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ScrollArea, Tabs } from 'frappe-ui'
import AccountSettings from '@/components/settings/AccountSettings.vue'
import SavedPostsSettings from '@/components/settings/SavedPostsSettings.vue'

// The mobile Settings page. Desktop uses SettingsModal instead (see router.js).
const route = useRoute()
const router = useRouter()

const tabs = [{ label: 'Account' }, { label: 'Saved' }]

// The tab lives in the URL (?tab=saved). Opening a saved post leaves this
// page, so the back button needs the URL to bring the same tab back.
const tab = ref(Math.max(0, tabs.findIndex((t) => t.label.toLowerCase() === route.query.tab)))

watch(tab, (index) => {
  const slug = index === 0 ? undefined : tabs[index].label.toLowerCase()
  if ((route.query.tab || undefined) === slug) return
  const query = { ...route.query }
  if (slug) query.tab = slug
  else delete query.tab
  router.replace({ query })
})
</script>

<style scoped>
/* Tabs' own tablist has a built-in horizontal px-5. Zero it, and use
   Figma's 32px gap and 33px bar height, so the labels line up with the rows
   below. */
.settings-tabs :deep([role='tablist']) {
  padding: 0;
  gap: 32px;
}
.settings-tabs :deep([role='tab']) {
  padding-top: 8px;
  padding-bottom: 8px;
}

/* Same nested-scrollbar fix as ProfilePosts.vue's tabs. */
.settings-tabs :deep([role='tabpanel']) {
  overflow: visible;
}
</style>
