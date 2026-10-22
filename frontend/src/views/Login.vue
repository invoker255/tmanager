<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import AuthLayout from '../components/AuthLayout.vue'
import { authApi, usersApi, extractError } from '../services/api'
import { auth } from '../stores/auth'
import { applyTheme } from '../stores/theme'

const router = useRouter()

const form = reactive({ username: '', password: '' })
const loading = ref(false)
const error = ref('')
const info = ref('')
const needsVerification = ref(false)
const email = ref('')
const resending = ref(false)

async function submit() {
  error.value = ''
  info.value = ''
  needsVerification.value = false
  loading.value = true
  try {
    const { data } = await authApi.login({ username: form.username, password: form.password })
    if (!data.token) {
      error.value = 'The server did not return an access token.'
      return
    }
    auth.setToken(data.token)
    try {
      const settings = await usersApi.settings()
      if (settings.data.theme) applyTheme(settings.data.theme)
    } catch (e) {
      error.value = ''
    }
    router.push({ name: 'dashboard' })
  } catch (e) {
        needsVerification.value = e.response?.data?.code === 'email_not_verified'
    error.value = needsVerification.value
      ? 'Your email is not verified yet. Open the link in the email we sent, or request a new one below.'
      : extractError(e, 'Incorrect username or password.')
  } finally {
    loading.value = false
  }
}

async function resend() {
  error.value = ''
  info.value = ''
  resending.value = true
  try {
    await authApi.resendVerification(email.value)
    info.value = 'Verification email sent. Check your inbox.'
  } catch (e) {
    error.value = extractError(e)
  } finally {
    resending.value = false
  }
}
</script>

<template>
  <AuthLayout title="Log in" subtitle="Welcome back.">
    <form class="space-y-6" @submit.prevent="submit">
      <p v-if="info" class="msg-ok" role="status">{{ info }}</p>
      <p v-if="error" class="msg-error" role="alert">{{ error }}</p>
      <div>
        <label class="label" for="username">Username</label>
        <input id="username" v-model.trim="form.username" class="field" type="text" autocomplete="username" required />
      </div>
      <div>
        <label class="label" for="password">Password</label>
        <input id="password" v-model="form.password" class="field" type="password" autocomplete="current-password" required />
      </div>
      <button class="btn w-full" type="submit" :disabled="loading">{{ loading ? 'Logging in' : 'Log in' }}</button>
    </form>

    <form v-if="needsVerification" class="mt-8 space-y-4" @submit.prevent="resend">
      <div>
        <label class="label" for="verify-email">Email you registered with</label>
        <input id="verify-email" v-model.trim="email" class="field" type="email" autocomplete="email" required />
      </div>
      <button class="link-btn" type="submit" :disabled="resending">{{ resending ? 'Sending' : 'Send a new verification email' }}</button>
    </form>

    <p class="mt-8 text-sm text-ink/60">
      New here?
      <RouterLink to="/register" class="font-medium text-accent underline-offset-4 hover:underline">Create an account</RouterLink>
    </p>
  </AuthLayout>
</template>
