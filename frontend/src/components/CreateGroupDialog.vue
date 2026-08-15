<template>
  <Dialog v-model:open="open" size="lg" title="New group">
    <template #default>
      <div class="flex flex-col gap-4">
        <FormControl v-model="title" label="Group name" placeholder="e.g. Design Team" />
        <div>
          <span class="mb-1.5 block text-sm-medium text-ink-gray-7">Members</span>
          <p class="mb-2 text-p-sm text-ink-gray-5">
            They'll get an invite to join — added once they accept, not immediately.
          </p>
          <PeoplePicker v-model="selected" />
        </div>
      </div>
    </template>
    <template #actions="{ close }">
      <div class="flex justify-end gap-2">
        <Button variant="outline" label="Cancel" @click="close" />
        <Button
          variant="solid"
          theme="gray"
          label="Create group"
          :loading="createGroup.loading"
          :disabled="!canCreate"
          @click="submit"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { Button, Dialog, FormControl, toast, useCall } from 'frappe-ui'
import PeoplePicker from './PeoplePicker.vue'

const open = defineModel({ default: false })
const emit = defineEmits(['created'])

const title = ref('')
const selected = ref([])

watch(open, (isOpen) => {
  if (isOpen) {
    title.value = ''
    selected.value = []
  }
})

const canCreate = computed(() => Boolean(title.value.trim()) && selected.value.length > 0)

const createGroup = useCall({
  url: '/api/v2/method/my_new_app.chat.create_group',
  method: 'POST',
  immediate: false,
  onSuccess: (data) => {
    open.value = false
    emit('created', data.conversation)
  },
  onError: (err) => toast.error(err.message),
})

function submit() {
  createGroup.submit({ title: title.value.trim(), members: selected.value.map((p) => p.name) })
}
</script>
