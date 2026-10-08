<script setup>
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import AppHeader from './components/AppHeader.vue'
import { auth } from './stores/auth'
import { applyTheme } from './stores/theme'
import { usersApi } from './services/api'

const route = useRoute()
const showHeader = computed(() => auth.isAuthenticated && route.meta.requiresAuth)

onMounted(async () => {
  if (!auth.isAuthenticated) return
  try {
    const { data } = await usersApi.settings()
    if (data.theme) applyTheme(data.theme)
  } catch (e) {
    return
  }
})
</script>

<template>
  <AppHeader v-if="showHeader" />
  <RouterView />
</template>
