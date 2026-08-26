<template>
  <AuthCard
    v-if="signupSubmittedTo"
    title="Check your email"
    :subtitle="`We sent a verification link to ${signupSubmittedTo}. Click it to finish creating your account.`"
  >
    <Button
      class="w-full justify-center"
      variant="outline"
      theme="gray"
      label="Use a different email"
      @click="signupSubmittedTo = null"
    />

    <template #footer>
      Already verified?
      <router-link class="font-medium text-ink-gray-9 underline" :to="{ name: 'Login' }">
        Log in.
      </router-link>
    </template>
  </AuthCard>

  <AuthCard
    v-else
    title="Create your account"
    subtitle="Write, share, and connect — without the noise."
  >
    <form @submit.prevent="submit">
      <FormControl type="text" label="Username" placeholder="janedoe" v-model="username" required autofocus />

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
import AuthCard from '@/components/AuthCard.vue'
import GoogleIcon from '@/components/GoogleIcon.vue'

const username = ref('')
const email = ref('')
const password = ref('')
// Set once signup succeeds, to the address the link was actually sent to -
// switches the card over to "check your email" instead of logging straight
// in, since the account doesn't exist yet at this point (see api.signup:
// nothing is created until the emailed link is clicked).
const signupSubmittedTo = ref(null)

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
    signupSubmittedTo.value = email.value
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
