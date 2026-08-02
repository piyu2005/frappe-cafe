<template>
  <AuthCard
    :title="`Log in to ${APP_NAME}`"
    subtitle="Write, share, and connect — without the noise."
  >
    <form @submit.prevent="submit">
      <FormControl type="email" label="Email" placeholder="name@example.com" v-model="email" required />

      <FormControl
        class="mt-4"
        type="password"
        label="Password"
        placeholder="••••••••"
        v-model="password"
        required
      />

      <ErrorMessage class="mt-3" :message="error" />

      <Button
        class="mt-4 w-full justify-center"
        variant="solid"
        theme="gray"
        type="submit"
        :loading="loading"
        label="Log in"
      />

      <Button class="mt-2 w-full justify-center" variant="outline" type="button" @click="continueWithGoogle">
        <template #prefix>
          <GoogleIcon />
        </template>
        Continue with Google
      </Button>
    </form>

    <template #footer>
      New member?
      <router-link class="font-medium text-ink-gray-9 underline" :to="{ name: 'Signup' }">
        Create a new account.
      </router-link>
    </template>
  </AuthCard>
</template>

<script setup>
import { ref } from 'vue'
import { Button, ErrorMessage, FormControl, toast, useCall } from 'frappe-ui'
import { useRouter } from 'vue-router'
import { login } from '@/data/session'
import AuthCard from '@/components/AuthCard.vue'
import GoogleIcon from '@/components/GoogleIcon.vue'
import { APP_NAME } from '@/utils/appName'

const router = useRouter()

const email = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

const googleLoginUrl = useCall({
  url: '/api/v2/method/my_new_app.api.get_google_login_url',
  method: 'POST',
  immediate: false,
  onSuccess(url) {
    if (url) {
      window.location.href = url
    } else {
      toast.info('Google sign-in is not configured yet')
    }
  },
})

async function submit() {
  if (!email.value || !password.value) return
  loading.value = true
  error.value = ''
  try {
    await login(email.value, password.value)
    router.replace('/')
  } catch (e) {
    error.value = e.message || 'Invalid email or password'
  } finally {
    loading.value = false
  }
}

function continueWithGoogle() {
  googleLoginUrl.submit({})
}
</script>
