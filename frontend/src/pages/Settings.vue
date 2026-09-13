<template>
  <PageHeader v-if="!isMobile">
    <Breadcrumbs :items="[{ label: APP_NAME, route: '/' }, { label: 'Settings' }]" />
    <Button variant="solid" theme="gray" icon-left="lucide-plus" label="New Post" route="/write" />
  </PageHeader>
  <ScrollArea class="h-full">
    <div class="mx-auto max-w-[600px] px-4 py-6 sm:px-0 sm:pt-12 sm:pb-12">
      <SettingsPanel />
    </div>
  </ScrollArea>
</template>

<script setup>
import { Breadcrumbs, Button, PageHeader, ScrollArea } from 'frappe-ui'
import SettingsPanel from '@/components/SettingsPanel.vue'
import { APP_NAME } from '@/utils/appName'
import { useIsMobile } from '@/composables/useIsMobile'

const isMobile = useIsMobile()
</script>
