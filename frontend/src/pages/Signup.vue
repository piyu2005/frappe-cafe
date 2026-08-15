<template>
  <AuthCard
    title="Create your account"
    subtitle="Write, share, and connect — without the noise."
  >
    <form @submit.prevent="submit">
      <FormControl type="text" label="Username" placeholder="janedoe" v-model="username" required />

      <FormControl
        class="mt-4"
        type="email"
        label="Email"
        placeholder="name@example.com"
        v-model="email"
        required
      />

      <FormControl
        class="mt-4"
        type="password"
        label="Password"
        placeholder="••••••••"
        v-model="password"
        required
      />

      <ErrorMessage class="mt-3" :message="signup.error?.message" />

      <Button
        class="mt-4 w-full justify-center"
        variant="solid"
        theme="gray"
        type="submit"
        :loading="signup.loading"
        label="Create account"
      />

      <Button class="mt-2 w-full justify-center" variant="outline" type="button" @click="continueWithGoogle">
        <template #prefix>
          <GoogleIcon />
        </template>
        Continue with Google
      </Button>
    </form>

    <template #footer>
      Already have an account?
      <router-link class="font-medium text-ink-gray-9 underline" :to="{ name: 'Login' }">
        Log in.
      </router-link>
    </template>
  </AuthCard>
</template>

<script setup>
import { ref } from 'vue'
import { Button, ErrorMessage, FormControl, toast, useCall } from 'frappe-ui'
import { useRouter } from 'vue-router'
import { session } from '@/data/session'
import AuthCard from '@/components/AuthCard.vue'
import GoogleIcon from '@/components/GoogleIcon.vue'

const router = useRouter()

const username = ref('')
const email = ref('')
const password = ref('')

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

const signup = useCall({
  url: '/api/v2/method/my_new_app.api.signup',
  method: 'POST',
  immediate: false,
  onSuccess() {
    session.refresh()
    router.replace('/')
  },
})

function submit() {
  if (!username.value || !email.value || !password.value) return
  signup.submit({ email: email.value, password: password.value, username: username.value })
}

function continueWithGoogle() {
  googleLoginUrl.submit({})
}
</script>
