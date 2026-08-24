<template>
  <AuthCard
    :title="verify.error ? 'Verification failed' : 'Verifying your email…'"
    :subtitle="verify.error ? '' : 'Just a moment while we confirm your account.'"
  >
    <LoadingText v-if="verify.loading || (!verify.error && !verified)" :lines="2" />

    <template v-else-if="verify.error">
      <ErrorMessage :message="verify.error.message" />
      <Button class="mt-4 w-full justify-center" variant="solid" theme="gray" label="Back to sign up" route="/signup" />
    </template>

    <p v-else class="text-p-sm text-ink-gray-5">Redirecting…</p>

    <template #footer>
      <router-link class="font-medium text-ink-gray-9 underline" :to="{ name: 'Login' }"> Back to log in. </router-link>
    </template>
  </AuthCard>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Button, ErrorMessage, LoadingText, useCall } from 'frappe-ui'
import { session } from '@/data/session'
import AuthCard from '@/components/AuthCard.vue'

const route = useRoute()
const router = useRouter()
const verified = ref(false)

const verify = useCall({
  url: '/api/v2/method/my_new_app.api.verify_email',
  method: 'POST',
  immediate: false,
})

// No form to submit here - the link itself, tied to a one-time key, is the
// entire action, so this fires as soon as the page has it (same idea as
// ResetPassword using its own key on submit, just with nothing for the
// visitor to fill in first).
onMounted(async () => {
  await verify.submit({ key: route.query.key })
  if (!verify.error) {
    verified.value = true
    await session.refresh()
    router.replace('/')
  }
})
</script>
