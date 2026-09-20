<template>
  <div>
    <div v-if="modelValue.length" class="mb-2 flex flex-wrap gap-1.5">
      <span
        v-for="p in modelValue"
        :key="p.name"
        class="flex items-center gap-1.5 rounded-full bg-surface-gray-2 py-1 pl-1 pr-2 text-sm text-ink-gray-8"
      >
        <Avatar :image="p.user_image" :label="p.full_name" size="sm" />
        {{ p.full_name }}<span v-if="p.username" class="text-ink-gray-5">@{{ p.username }}</span>
        <span
          class="lucide-x size-3 cursor-pointer text-ink-gray-5 hover:text-ink-gray-8"
          aria-hidden="true"
          @click="remove(p)"
        />
      </span>
    </div>

    <TextInput v-model="query" placeholder="Search by name">
      <template #prefix>
        <span class="lucide-search size-4 text-ink-gray-5" aria-hidden="true" />
      </template>
    </TextInput>

    <div v-if="query.trim()" class="mt-2 max-h-48 overflow-y-auto rounded-md border border-outline-gray-1">
      <LoadingText v-if="search.loading && !search.data" class="p-3" :lines="3" />
      <p v-else-if="!filteredResults.length" class="p-3 text-center text-p-sm text-ink-gray-5">
        No people found.
      </p>
      <button
        v-for="p in filteredResults"
        :key="p.name"
        type="button"
        class="flex w-full items-center gap-3 px-3 py-2 text-left hover:bg-surface-gray-1"
        @click="add(p)"
      >
        <Avatar :image="p.user_image" :label="p.full_name" size="sm" />
        <div class="min-w-0 flex-1">
          <span class="truncate text-sm text-ink-gray-8">{{ p.full_name }}</span>
          <span v-if="p.username" class="ml-1.5 truncate text-xs text-ink-gray-5">@{{ p.username }}</span>
        </div>
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { Avatar, LoadingText, TextInput, useCall } from 'frappe-ui'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  // ids to leave out of results entirely — already a member, e.g.
  excludeUsers: { type: Array, default: () => [] },
})
const emit = defineEmits(['update:modelValue'])

const query = ref('')

const search = useCall({
  url: '/api/v2/method/my_new_app.chat.search_people_to_message',
  params: () => ({ query: query.value }),
  immediate: false,
})

let debounceTimer = null
watch(query, (val) => {
  clearTimeout(debounceTimer)
  if (!val.trim()) return
  debounceTimer = setTimeout(() => search.reload(), 200)
})

const filteredResults = computed(() => {
  const selectedIds = new Set(props.modelValue.map((p) => p.name))
  const excluded = new Set(props.excludeUsers)
  return (search.data || []).filter((p) => !selectedIds.has(p.name) && !excluded.has(p.name))
})

function add(person) {
  emit('update:modelValue', [...props.modelValue, person])
  query.value = ''
}

function remove(person) {
  emit(
    'update:modelValue',
    props.modelValue.filter((p) => p.name !== person.name),
  )
}
</script>
