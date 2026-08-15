<template>
  <div class="w-72">
    <div class="border-b border-outline-gray-1 p-2">
      <input
        v-model="query"
        type="text"
        placeholder="Search emoji"
        class="w-full rounded border-0 bg-surface-gray-2 px-2.5 py-1.5 text-sm text-ink-gray-8 placeholder:text-ink-gray-4 focus:outline-none focus:ring-1 focus:ring-outline-gray-3"
      />
    </div>
    <div class="grid max-h-56 grid-cols-8 gap-0.5 overflow-y-auto p-1.5">
      <button
        v-for="e in filtered"
        :key="e.name"
        type="button"
        :title="e.name"
        class="rounded p-1 text-lg hover:bg-surface-gray-2"
        @click="$emit('select', e.emoji)"
      >
        {{ e.emoji }}
      </button>
      <p v-if="!filtered.length" class="col-span-8 py-6 text-center text-p-sm text-ink-gray-5">
        No emoji found.
      </p>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
// The same gemoji-style dataset frappe-ui itself ships for the Editor's
// `:name:` emoji autocomplete — the full set any Frappe product (Raven
// included) draws from, not a hand-picked shortlist.
import emojis from '@/data/emojis.json'

defineEmits(['select'])

const query = ref('')
const filtered = computed(() => {
  const q = query.value.trim().toLowerCase()
  if (!q) return emojis
  return emojis.filter((e) => e.name.includes(q))
})
</script>
