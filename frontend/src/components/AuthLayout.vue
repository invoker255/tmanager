<script setup>
defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' }
})
</script>

<template>
  <main class="mx-auto flex min-h-screen max-w-sm flex-col justify-center px-5 py-12">
    <p class="text-lg font-semibold tracking-tight">Tasks</p>
    <h1 class="mt-10 text-3xl font-semibold tracking-tight">{{ title }}</h1>
    <p v-if="subtitle" class="mt-2 text-ink/60">{{ subtitle }}</p>
    <div class="mt-8">
      <slot />
    </div>
  </main>
</template>
