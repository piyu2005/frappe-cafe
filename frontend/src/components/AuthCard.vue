<template>
  <div class="flex min-h-screen w-screen items-center justify-center bg-surface-gray-1 px-4">
    <div class="w-full max-w-sm rounded-lg border border-outline-gray-1 bg-surface-base p-8 shadow-sm">
      <div class="mb-5 flex h-11 w-11 items-center justify-center rounded-xl bg-surface-gray-10">
        <span class="lucide-feather size-5 text-ink-base" aria-hidden="true" />
      </div>

      <h1 class="text-xl font-semibold text-ink-gray-9">{{ title }}</h1>
      <p class="mt-1 text-p-sm text-ink-gray-5">{{ subtitle }}</p>

      <div class="mt-6">
        <slot />
      </div>

      <div class="mt-6 text-center text-sm text-ink-gray-5">
        <slot name="footer" />
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: String,
  subtitle: String,
})
</script>
