<template>
  <AuthCard title="Set a new password" subtitle="Choose a strong password you haven't used before.">
    <form @submit.prevent="submit">
      <FormControl
        type="password"
        label="New password"
        placeholder="••••••••"
        v-model="newPassword"
        required
      />

      <FormControl
        class="mt-4"
        type="password"
        label="Confirm new password"
        placeholder="••••••••"
        v-model="confirmPassword"
        required
      />

      <ErrorMessage class="mt-3" :message="error" />

      <Button
        class="mt-4 w-full justify-center"
        variant="solid"
        theme="gray"
        type="submit"
        :loading="updatePassword.loading"
        label="Reset password"
      />
    </form>

    <template #footer>
      <router-link class="font-medium text-ink-gray-9 underline" :to="{ name: 'Login' }"> Back to log in. </router-link>
    </template>
  </AuthCard>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Button, ErrorMessage, FormControl, useCall } from 'frappe-ui'
import { session } from '@/data/session'
import AuthCard from '@/components/AuthCard.vue'

const route = useRoute()
const router = useRouter()

const newPassword = ref('')
const confirmPassword = ref('')
const error = ref('')

// update_password also logs the user in on success (and, since it's not a
// System User, its own return value already resolves to this app's home
// page) — session.refresh() just picks up that already-established
// session rather than starting a separate login step.
const updatePassword = useCall({
  url: '/api/v2/method/frappe.core.doctype.user.user.update_password',
  method: 'POST',
  immediate: false,
  onSuccess: async () => {
    await session.refresh()
    router.replace('/')
  },
  // A missing/expired key comes back as an HTTP 410 with a plain message
  // body rather than a normal frappe.throw-shaped error (see
  // _get_user_for_update_password) — not worth parsing that shape just to
  // echo it; a generic explanation covers every real case here (link
  // already used, expired, or malformed).
  onError: () => {
    error.value = 'This link is invalid or has expired. Please request a new one.'
  },
})

function submit() {
  if (!newPassword.value || !confirmPassword.value) return
  if (newPassword.value !== confirmPassword.value) {
    error.value = "Passwords don't match"
    return
  }
  error.value = ''
  updatePassword.submit({ new_password: newPassword.value, key: route.query.key })
}
</script>
