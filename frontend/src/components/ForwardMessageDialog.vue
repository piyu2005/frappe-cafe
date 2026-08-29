<template>
  <Dialog v-model="open" size="lg" title="Forward message">
    <template #default>
      <div class="flex flex-col gap-2">
        <TextInput v-model="query" placeholder="Search by name">
          <template #prefix>
            <span class="lucide-search size-4 text-ink-gray-5" aria-hidden="true" />
          </template>
        </TextInput>

        <div class="max-h-72 overflow-y-auto rounded-md border border-outline-gray-1">
          <LoadingText v-if="peopleSearch.loading && !peopleSearch.data" class="p-3" :lines="3" />
          <p v-else-if="!results.length" class="p-3 text-center text-p-sm text-ink-gray-5">No matches found.</p>
          <button
            v-for="r in results"
            :key="r.key"
            type="button"
            class="flex w-full items-center gap-3 px-3 py-2 text-left hover:bg-surface-gray-1 disabled:opacity-50"
            :disabled="forwarding"
            @click="select(r)"
          >
            <Avatar :image="r.image" :label="r.label" size="sm" />
            <div class="min-w-0 flex-1">
              <span class="truncate text-sm text-ink-gray-8">{{ r.label }}</span>
              <span v-if="r.username" class="ml-1.5 truncate text-xs text-ink-gray-5">@{{ r.username }}</span>
            </div>
          </button>
        </div>
      </div>
    </template>
    <template #actions="{ close }">
      <div class="flex justify-end">
        <Button variant="outline" label="Cancel" @click="close" />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
// Single-select "who to forward to", built to match PeoplePicker's
// search-as-you-type feel (used by New Group's member picker) rather than
// the combobox-popup pattern the first version of this dialog used — typing
// a name should show live matches directly under the field, not require
// opening a separate dropdown first.
import { computed, ref, watch } from 'vue'
import { Avatar, Button, Dialog, LoadingText, TextInput, call, toast, useCall } from 'frappe-ui'

const props = defineProps({
  message: { type: Object, default: null },
  conversations: { type: Array, default: () => [] },
  excludeConversation: { type: String, default: null },
})
const open = defineModel({ default: false })
const emit = defineEmits(['forwarded'])

const query = ref('')
const forwarding = ref(false)

const peopleSearch = useCall({
  url: '/api/v2/method/my_new_app.chat.search_people_to_message',
  params: () => ({ query: query.value }),
  immediate: false,
})

let debounceTimer = null
watch(query, () => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => peopleSearch.reload(), 200)
})

watch(open, (isOpen) => {
  if (!isOpen) return
  query.value = ''
  peopleSearch.reload()
})

// Existing conversations (including groups) first, then anyone else on the
// platform — a person who already has a DM is left out of the second group
// so they don't show up twice under two different labels for the same chat.
const results = computed(() => {
  const q = query.value.trim().toLowerCase()
  const existingDmUsers = new Set(props.conversations.map((c) => c.other_user).filter(Boolean))

  const conversationResults = props.conversations
    .filter((c) => c.conversation !== props.excludeConversation)
    .filter((c) => !q || c.display_name.toLowerCase().includes(q))
    .map((c) => ({
      key: `conversation:${c.conversation}`,
      kind: 'conversation',
      id: c.conversation,
      label: c.display_name,
      image: c.display_image,
    }))

  const peopleResults = (peopleSearch.data || [])
    .filter((p) => !existingDmUsers.has(p.name))
    .map((p) => ({
      key: `person:${p.name}`,
      kind: 'person',
      id: p.name,
      label: p.full_name,
      username: p.username,
      image: p.user_image,
    }))

  return [...conversationResults, ...peopleResults]
})

async function select(r) {
  if (forwarding.value || !props.message) return
  forwarding.value = true
  try {
    const conversationId =
      r.kind === 'person' ? (await call('my_new_app.chat.start_dm', { other_user: r.id })).conversation : r.id
    await call('my_new_app.chat.forward_message', { message: props.message.name, conversation: conversationId })
    toast.success('Message forwarded')
    open.value = false
    emit('forwarded')
  } catch (err) {
    toast.error(err.message || 'Could not forward message')
  } finally {
    forwarding.value = false
  }
}
</script>
