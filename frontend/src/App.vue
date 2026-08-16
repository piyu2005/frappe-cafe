<template>
  <FrappeUIProvider>
    <router-view v-if="ready" />
    <!-- router-view renders nothing until the first navigation's guard
         resolves (router.beforeEach awaits verifySession() for protected
         routes) — without this, a fresh load on a slow connection is a
         blank white screen for that gap. router.isReady() resolves once
         after the very first navigation settles, so this never gates
         anything again afterwards. -->
    <div v-else class="flex h-screen items-center justify-center">
      <LoadingIndicator class="text-ink-gray-4" />
    </div>
  </FrappeUIProvider>
</template>

<script setup>
import { ref } from 'vue'
import { FrappeUIProvider, LoadingIndicator } from 'frappe-ui'
import router from './router'

const ready = ref(false)
router.isReady().then(() => {
  ready.value = true
})
</script>
