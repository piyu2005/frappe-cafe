<template>
  <AuthCard
    title="Create your account"
    subtitle="Write, share, and connect — without the noise."
  >
    <form v-if="step === 'details'" @submit.prevent="sendCode">
      <FormControl type="text" label="Username" placeholder="janedoe" v-model="username" required autofocus />

      <FormControl
        class="mt-4"
        type="email"
        label="Email"
        placeholder="name@example.com"
        v-model="email"
        required
      />

      <ErrorMessage class="mt-3" :message="sendCodeError" />

      <Button
        class="mt-4 w-full justify-center"
        variant="solid"
        theme="gray"
        type="submit"
        :loading="sendCodeLoading"
        label="Send verification code"
      />

      <Button class="mt-2 w-full justify-center" variant="outline" type="button" @click="continueWithGoogle">
        <template #prefix>
          <GoogleIcon />
        </template>
        Continue with Google
      </Button>
    </form>

    <form v-else @submit.prevent="verifyCode">
      <p class="text-p-sm text-ink-gray-5">We sent a 6 digit verification code to {{ email }}</p>

      <OtpInput ref="otpInput" v-model="code" class="mt-4" @complete="verifyCode" />

      <ErrorMessage class="mt-3" :message="verifyCodeError" />

      <Button
        class="mt-4 w-full justify-center"
        variant="solid"
        theme="gray"
        type="submit"
        :loading="verifyCodeLoading"
        label="Verify"
      />

      <p class="mt-3 text-center text-sm text-ink-gray-5">
        <button
          v-if="resendCooldown === 0"
          type="button"
          class="font-medium text-ink-gray-9 underline"
          @click="sendCode"
        >
          Resend code
        </button>
        <template v-else>Resend in {{ resendCooldown }} seconds</template>
      </p>
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
import { onBeforeUnmount, ref } from 'vue'
import { Button, ErrorMessage, FormControl, call, toast, useCall } from 'frappe-ui'
import { useRouter } from 'vue-router'
import { errorMessage, session } from '@/data/session'
import AuthCard from '@/components/AuthCard.vue'
import GoogleIcon from '@/components/GoogleIcon.vue'
import OtpInput from '@/components/OtpInput.vue'

const router = useRouter()

const step = ref('details') // 'details' | 'code'
const username = ref('')
const email = ref('')
const code = ref('')
const otpInput = ref(null)

const sendCodeError = ref('')
const verifyCodeError = ref('')

const RESEND_COOLDOWN_SEC = 25
const resendCooldown = ref(0)
let cooldownTimer = null

function startResendCooldown() {
  resendCooldown.value = RESEND_COOLDOWN_SEC
  clearInterval(cooldownTimer)
  cooldownTimer = setInterval(() => {
    resendCooldown.value -= 1
    if (resendCooldown.value <= 0) clearInterval(cooldownTimer)
  }, 1000)
}

onBeforeUnmount(() => clearInterval(cooldownTimer))

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

const sendCodeLoading = ref(false)

async function sendCode() {
  if (!username.value || !email.value || sendCodeLoading.value) return
  sendCodeLoading.value = true
  sendCodeError.value = ''
  try {
    await call('my_new_app.api.send_signup_code', { email: email.value, username: username.value })
    code.value = ''
    step.value = 'code'
    startResendCooldown()
    otpInput.value?.focus()
  } catch (e) {
    sendCodeError.value = errorMessage(e)
  } finally {
    sendCodeLoading.value = false
  }
}

const verifyCodeLoading = ref(false)

async function verifyCode() {
  if (code.value.length !== 6 || verifyCodeLoading.value) return
  verifyCodeLoading.value = true
  verifyCodeError.value = ''
  try {
    await call('my_new_app.api.verify_signup_code', { email: email.value, code: code.value })
    await session.refresh()
    router.replace('/')
  } catch (e) {
    verifyCodeError.value = errorMessage(e, 'Incorrect code. Please try again.')
    code.value = ''
  } finally {
    verifyCodeLoading.value = false
  }
}

function continueWithGoogle() {
  googleLoginUrl.submit({})
}
</script>
