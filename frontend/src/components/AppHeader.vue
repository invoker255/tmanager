<script setup>
import { useRouter } from 'vue-router'
import { auth } from '../stores/auth'

const router = useRouter()

function logout() {
  auth.clear()
  router.push({ name: 'login' })
}
</script>

<template>
  <header class="border-b border-ink/10">
    <div class="mx-auto flex max-w-2xl items-center justify-between px-5 py-4">
      <RouterLink to="/dashboard" class="text-lg font-semibold tracking-tight">Tasks</RouterLink>
      <nav class="flex items-center gap-6 text-sm">
        <RouterLink to="/settings" class="text-ink/60 hover:text-ink" active-class="!text-ink font-medium">Settings</RouterLink>
        <button type="button" class="text-ink/60 hover:text-ink" @click="logout">Log out</button>
      </nav>
    </div>
  </header>
</template>
