<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import AuthLayout from '../components/AuthLayout.vue'
import { authApi, extractError } from '../services/api'

const route = useRoute()
const state = ref('loading')
const message = ref('')

onMounted(async () => {
  try {
    await authApi.verifyEmail(route.params.uid, route.params.token)
    state.value = 'success'
  } catch (e) {
    message.value = extractError(e, 'This link is invalid or has expired.')
    state.value = 'error'
  }
})
</script>

<template>
  <AuthLayout title="Email verification">
    <p v-if="state === 'loading'" class="text-ink/60">Checking your link</p>
    <div v-else-if="state === 'success'" class="space-y-6">
      <p class="msg-ok" role="status">Your email is verified. You can log in now.</p>
      <RouterLink to="/login" class="btn w-full">Log in</RouterLink>
    </div>
    <div v-else class="space-y-6">
      <p class="msg-error" role="alert">{{ message }}</p>
      <p class="text-sm text-ink/60">Try logging in. If your email is still unverified, you will be able to request a new link.</p>
      <RouterLink to="/login" class="btn w-full">Go to log in</RouterLink>
    </div>
  </AuthLayout>
</template>
