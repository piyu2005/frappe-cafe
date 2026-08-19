<template>
  <AuthCard
    :title="sent ? 'Check your email' : 'Reset your password'"
    :subtitle="
      sent
        ? `If ${email} is registered with us, we've sent password reset instructions to it.`
        : 'Enter your email and we\'ll send you a link to reset your password.'
    "
  >
    <form v-if="!sent" @submit.prevent="submit">
      <FormControl type="email" label="Email" placeholder="name@example.com" v-model="email" required />

      <ErrorMessage class="mt-3" :message="resetPassword.error?.message" />

      <Button
        class="mt-4 w-full justify-center"
        variant="solid"
        theme="gray"
        type="submit"
        :loading="resetPassword.loading"
        label="Send reset link"
      />
    </form>

    <Button v-else class="w-full justify-center" variant="outline" label="Send again" @click="sent = false" />

    <template #footer>
      <router-link class="font-medium text-ink-gray-9 underline" :to="{ name: 'Login' }"> Back to log in. </router-link>
    </template>
  </AuthCard>
</template>

<script setup>
import { ref } from 'vue'
import { Button, ErrorMessage, FormControl, useCall } from 'frappe-ui'
import AuthCard from '@/components/AuthCard.vue'

const email = ref('')
const sent = ref(false)

// frappe.core's reset_password always responds with the same generic
// "if this email is registered..." message regardless of whether the
// account actually exists (prevents enumerating registered emails by
// response) — sent=true is shown on any successful response, not just when
// a matching account was found.
const resetPassword = useCall({
  url: '/api/v2/method/frappe.core.doctype.user.user.reset_password',
  method: 'POST',
  immediate: false,
  onSuccess() {
    sent.value = true
  },
})

function submit() {
  if (!email.value) return
  resetPassword.submit({ user: email.value })
}
</script>
