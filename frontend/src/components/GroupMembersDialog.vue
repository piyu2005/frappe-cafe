<template>
  <Dialog v-model:open="open" size="lg" title="Group info">
    <template #default>
      <div class="flex flex-col gap-5">
        <FormControl
          v-if="isAdmin"
          v-model="titleDraft"
          label="Group name"
          @blur="commitRename"
          @keydown.enter="commitRename"
        />
        <div v-else>
          <span class="mb-1 block text-sm-medium text-ink-gray-7">Group name</span>
          <p class="text-p-base text-ink-gray-8">{{ groupTitle }}</p>
        </div>

        <div v-if="isAdmin">
          <span class="mb-1.5 block text-sm-medium text-ink-gray-7">Add people</span>
          <PeoplePicker v-model="toInvite" :exclude-users="memberIds" />
          <Button
            v-if="toInvite.length"
            class="mt-2"
            variant="outline"
            :label="toInvite.length > 1 ? 'Send invites' : 'Send invite'"
            :loading="inviteCall.loading"
            @click="sendInvites"
          />
        </div>

        <div>
          <span class="mb-1.5 block text-sm-medium text-ink-gray-7">
            Members — {{ members.data?.members?.length || 0 }}
          </span>
          <div class="divide-y divide-outline-gray-1 rounded-md border border-outline-gray-1">
            <div v-for="m in members.data?.members" :key="m.name" class="flex items-center gap-3 px-3 py-2.5">
              <Avatar :image="m.user_image" :label="m.full_name" size="md" />
              <div class="min-w-0 flex-1">
                <div class="flex items-center gap-1.5">
                  <span class="truncate text-sm-medium text-ink-gray-9">{{ m.full_name }}</span>
                  <Badge v-if="m.is_admin" variant="subtle" theme="gray" size="sm" label="Admin" />
                  <Badge v-if="m.user === session.user" variant="subtle" theme="gray" size="sm" label="You" />
                </div>
              </div>
              <Dropdown v-if="isAdmin && m.user !== session.user" :options="memberOptions(m)">
                <Button variant="ghost" icon="lucide-more-horizontal" />
              </Dropdown>
            </div>
          </div>
        </div>

        <div v-if="isAdmin && members.data?.pending_invites?.length">
          <span class="mb-1.5 block text-sm-medium text-ink-gray-7">Pending invites</span>
          <div class="divide-y divide-outline-gray-1 rounded-md border border-outline-gray-1">
            <div
              v-for="p in members.data.pending_invites"
              :key="p.name"
              class="flex items-center gap-3 px-3 py-2.5"
            >
              <Avatar :image="p.user_image" :label="p.full_name" size="md" />
              <span class="min-w-0 flex-1 truncate text-sm-medium text-ink-gray-9">{{ p.full_name }}</span>
              <Button
                variant="ghost"
                size="sm"
                label="Cancel"
                :loading="cancelInviteCall.loading"
                @click="cancelInvite(p.name)"
              />
            </div>
          </div>
        </div>
      </div>
    </template>
    <template #actions="{ close }">
      <div class="flex justify-between">
        <Button variant="outline" theme="red" label="Leave group" :loading="leaveCall.loading" @click="confirmLeave" />
        <Button variant="subtle" theme="gray" label="Close" @click="close" />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Avatar, Badge, Button, Dialog, Dropdown, FormControl, dialog, toast, useCall } from 'frappe-ui'
import { session } from '@/data/session'
import PeoplePicker from './PeoplePicker.vue'

const props = defineProps({
  conversation: { type: String, default: '' },
  groupTitle: { type: String, default: '' },
})
const open = defineModel({ default: false })
const emit = defineEmits(['renamed', 'left'])

const router = useRouter()

const members = useCall({
  url: '/api/v2/method/my_new_app.chat.list_group_members',
  params: () => ({ conversation: props.conversation }),
  immediate: false,
})

const titleDraft = ref(props.groupTitle)
const toInvite = ref([])

watch(open, (isOpen) => {
  if (isOpen) {
    members.reload()
    titleDraft.value = props.groupTitle
    toInvite.value = []
  }
})

const isAdmin = computed(() => members.data?.my_is_admin || false)
const memberIds = computed(() => (members.data?.members || []).map((m) => m.user))

const renameCall = useCall({
  url: '/api/v2/method/my_new_app.chat.rename_group',
  method: 'POST',
  immediate: false,
  onSuccess: () => emit('renamed', titleDraft.value),
  onError: (err) => toast.error(err.message),
})

function commitRename() {
  const value = titleDraft.value.trim()
  if (!value || value === props.groupTitle) return
  renameCall.submit({ conversation: props.conversation, title: value })
}

const inviteCall = useCall({
  url: '/api/v2/method/my_new_app.chat.invite_to_group',
  method: 'POST',
  immediate: false,
  onError: (err) => toast.error(err.message),
})

async function sendInvites() {
  for (const person of toInvite.value) {
    await inviteCall.submit({ conversation: props.conversation, user: person.name })
  }
  toast.success(toInvite.value.length > 1 ? 'Invites sent' : 'Invite sent')
  toInvite.value = []
  members.reload()
}

const cancelInviteCall = useCall({
  url: '/api/v2/method/my_new_app.chat.cancel_group_invite',
  method: 'POST',
  immediate: false,
  onSuccess: () => members.reload(),
})

function cancelInvite(name) {
  cancelInviteCall.submit({ name })
}

const removeCall = useCall({
  url: '/api/v2/method/my_new_app.chat.remove_group_member',
  method: 'POST',
  immediate: false,
  onSuccess: () => members.reload(),
  onError: (err) => toast.error(err.message),
})

const adminCall = useCall({
  url: '/api/v2/method/my_new_app.chat.set_group_admin',
  method: 'POST',
  immediate: false,
  onSuccess: () => members.reload(),
  onError: (err) => toast.error(err.message),
})

function memberOptions(m) {
  return [
    m.is_admin
      ? {
          label: 'Remove as admin',
          icon: 'lucide-shield-off',
          onClick: () => adminCall.submit({ conversation: props.conversation, user: m.user, is_admin: 0 }),
        }
      : {
          label: 'Make admin',
          icon: 'lucide-shield',
          onClick: () => adminCall.submit({ conversation: props.conversation, user: m.user, is_admin: 1 }),
        },
    {
      label: 'Remove from group',
      icon: 'lucide-user-minus',
      onClick: () =>
        dialog.confirm({
          title: 'Remove this member?',
          message: `${m.full_name} will be removed from the group.`,
          theme: 'red',
          confirmLabel: 'Remove',
          onConfirm: () => removeCall.submit({ conversation: props.conversation, user: m.user }),
        }),
    },
  ]
}

const leaveCall = useCall({
  url: '/api/v2/method/my_new_app.chat.leave_group',
  method: 'POST',
  immediate: false,
  onSuccess: () => {
    open.value = false
    emit('left')
    router.replace({ name: 'Messages' })
  },
  onError: (err) => toast.error(err.message),
})

function confirmLeave() {
  dialog.confirm({
    title: 'Leave this group?',
    message: 'You can only rejoin if someone invites you again.',
    theme: 'red',
    confirmLabel: 'Leave',
    onConfirm: () => leaveCall.submit({ conversation: props.conversation }),
  })
}
</script>
