<template>
  <!-- Frappe core redirects an unauthenticated Desk visit to this same
       "/login" route, tagged with "redirect-to" (frappe/www/login.py) -
       the only way left for a System User (Administrator, etc.) to reach a
       password field at all, now that the passwordless flow below has none
       or any other page in this app to type one into. -->
  <AuthCard v-if="isSystemLogin" title="System login" subtitle="For Frappe Desk access.">
    <form @submit.prevent="submitSystemLogin">
      <FormControl type="text" label="Username" placeholder="Administrator" v-model="sysUsername" required autofocus />

      <FormControl class="mt-4" type="password" label="Password" v-model="sysPassword" required />

      <ErrorMessage class="mt-3" :message="sysLoginError" />

      <Button
        class="mt-4 w-full justify-center"
        variant="solid"
        theme="gray"
        type="submit"
        :loading="sysLoginLoading"
        label="Log in"
      />
    </form>

    <template #footer>
      <router-link class="font-medium text-ink-gray-9 underline" :to="{ name: 'Login' }">
        Back to {{ APP_NAME }} login.
      </router-link>
    </template>
  </AuthCard>

  <AuthCard
    v-else
    :title="`Log in to ${APP_NAME}`"
    subtitle="Write, share, and connect."
  >
    <form v-if="step === 'email'" @submit.prevent="sendCode">
      <FormControl type="email" label="Email" placeholder="name@example.com" v-model="email" required autofocus />

      <ErrorMessage class="mt-3" :message="sendCodeError" />
      <p v-if="showSignupLink" class="mt-2 text-sm text-ink-gray-5">
        <router-link class="font-medium text-ink-gray-9 underline" :to="{ name: 'Signup' }">
          Create one.
        </router-link>
      </p>

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
      New member?
      <router-link class="font-medium text-ink-gray-9 underline" :to="{ name: 'Signup' }">
        Create a new account.
      </router-link>
    </template>
  </AuthCard>
</template>

<script setup>
import { computed, onBeforeUnmount, ref } from 'vue'
import { Button, call, ErrorMessage, FormControl, toast, useCall } from 'frappe-ui'
import { useRoute, useRouter } from 'vue-router'
import { errorMessage, sendLoginCode, verifyLoginCode } from '@/data/session'
import AuthCard from '@/components/AuthCard.vue'
import GoogleIcon from '@/components/GoogleIcon.vue'
import OtpInput from '@/components/OtpInput.vue'
import { APP_NAME } from '@/utils/appName'

const route = useRoute()
const router = useRouter()

const isSystemLogin = computed(() => !!route.query['redirect-to'])
const sysUsername = ref('')
const sysPassword = ref('')
const sysLoginLoading = ref(false)
const sysLoginError = ref('')

// Only a same-origin, relative path is ever followed - a bare query param
// off Frappe's own redirect isn't trustworthy enough to hand straight to
// window.location (a crafted "/login?redirect-to=https://evil.com" link
// would otherwise send a successful admin login somewhere else entirely).
function safeRedirectTarget() {
  let target = route.query['redirect-to']
  if (typeof target === 'string' && target.startsWith('/') && !target.startsWith('//')) {
    return target
  }
  return '/desk'
}

async function submitSystemLogin() {
  if (!sysUsername.value || !sysPassword.value || sysLoginLoading.value) return
  sysLoginLoading.value = true
  sysLoginError.value = ''
  try {
    await call('login', { usr: sysUsername.value, pwd: sysPassword.value })
    window.location.href = safeRedirectTarget()
  } catch (e) {
    sysLoginError.value = errorMessage(e, 'Invalid username or password')
  } finally {
    sysLoginLoading.value = false
  }
}

const step = ref('email') // 'email' | 'code'
const email = ref('')
const code = ref('')
const otpInput = ref(null)

const sendCodeLoading = ref(false)
const sendCodeError = ref('')
const showSignupLink = ref(false)

const verifyCodeLoading = ref(false)
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

async function sendCode() {
  if (!email.value || sendCodeLoading.value) return
  sendCodeLoading.value = true
  sendCodeError.value = ''
  showSignupLink.value = false
  try {
    await sendLoginCode(email.value)
    code.value = ''
    step.value = 'code'
    startResendCooldown()
    otpInput.value?.focus()
  } catch (e) {
    sendCodeError.value = errorMessage(e)
    showSignupLink.value = sendCodeError.value.includes('No account found')
  } finally {
    sendCodeLoading.value = false
  }
}

async function verifyCode() {
  if (code.value.length !== 6 || verifyCodeLoading.value) return
  verifyCodeLoading.value = true
  verifyCodeError.value = ''
  try {
    await verifyLoginCode(email.value, code.value)
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
