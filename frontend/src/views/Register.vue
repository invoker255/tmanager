<script setup>
import { reactive, ref } from 'vue'
import AuthLayout from '../components/AuthLayout.vue'
import { authApi, extractError } from '../services/api'

const form = reactive({ username: '', email: '', password: '', confirm: '' })
const loading = ref(false)
const resending = ref(false)
const error = ref('')
const info = ref('')
const registered = ref(false)
const emailFailed = ref(false)

async function submit() {
  error.value = ''
  info.value = ''
  if (form.password !== form.confirm) {
    error.value = 'Passwords do not match.'
    return
  }
  loading.value = true
  try {
    const { data } = await authApi.register({ username: form.username, email: form.email, password: form.password })
    emailFailed.value = data.email_sent === false
    registered.value = true
  } catch (e) {
    error.value = extractError(e)
  } finally {
    loading.value = false
  }
}

async function resend() {
  error.value = ''
  info.value = ''
  resending.value = true
  try {
    await authApi.resendVerification(form.email)
    emailFailed.value = false
    info.value = 'Verification email sent again.'
  } catch (e) {
    error.value = extractError(e)
  } finally {
    resending.value = false
  }
}
</script>

<template>
  <AuthLayout title="Create account" subtitle="It takes a minute.">
    <div v-if="registered" class="space-y-6">
      <p v-if="emailFailed" class="msg-error" role="alert">
        Your account was created, but we could not send the verification email. Use the button below to try again.
      </p>
      <p v-else>We sent a verification link to <span class="font-medium">{{ form.email }}</span>. Open it to activate your account, then log in.</p>
      <p v-if="info" class="msg-ok" role="status">{{ info }}</p>
      <p v-if="error" class="msg-error" role="alert">{{ error }}</p>
      <RouterLink to="/login" class="btn w-full">Go to log in</RouterLink>
      <button type="button" class="link-btn" :disabled="resending" @click="resend">
        {{ resending ? 'Sending' : 'Send the email again' }}
      </button>
    </div>
    <template v-else>
      <form class="space-y-6" @submit.prevent="submit">
        <p v-if="error" class="msg-error" role="alert">{{ error }}</p>
        <div>
          <label class="label" for="username">Username</label>
          <input id="username" v-model.trim="form.username" class="field" type="text" autocomplete="username" required />
        </div>
        <div>
          <label class="label" for="email">Email</label>
          <input id="email" v-model.trim="form.email" class="field" type="email" autocomplete="email" required />
        </div>
        <div>
          <label class="label" for="password">Password</label>
          <input id="password" v-model="form.password" class="field" type="password" autocomplete="new-password" required />
          <p class="mt-2 text-sm text-ink/50">At least 8 characters, with upper and lower case letters, a number and a special character.</p>
        </div>
        <div>
          <label class="label" for="confirm">Repeat password</label>
          <input id="confirm" v-model="form.confirm" class="field" type="password" autocomplete="new-password" required />
        </div>
        <button class="btn w-full" type="submit" :disabled="loading">{{ loading ? 'Creating account' : 'Create account' }}</button>
      </form>
      <p class="mt-8 text-sm text-ink/60">
        Already registered?
        <RouterLink to="/login" class="font-medium text-accent underline-offset-4 hover:underline">Log in</RouterLink>
      </p>
    </template>
  </AuthLayout>
</template>