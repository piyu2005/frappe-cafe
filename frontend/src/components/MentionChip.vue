<template>
  <NodeViewWrapper as="span" class="inline">
    <HoverCard :hover-delay="0.4" side="bottom" align="start">
      <template #trigger>
        <span class="mention" data-type="mention">@{{ label }}</span>
      </template>
      <template #default>
        <div class="w-64 p-4">
          <div class="flex items-center gap-3">
            <Avatar :image="profile.data?.user_image" :label="profile.data?.full_name || label" size="3xl" />
            <div class="min-w-0">
              <div class="truncate text-base-medium text-ink-gray-9">
                {{ profile.data?.full_name || label }}
              </div>
              <div class="truncate text-p-sm text-ink-gray-5">{{ userId }}</div>
            </div>
          </div>
          <Button
            class="mt-4 w-full justify-center"
            variant="outline"
            label="Message"
            :loading="startDm.loading"
            @click="messageThisPerson"
          />
        </div>
      </template>
    </HoverCard>
  </NodeViewWrapper>
</template>

<script setup>
import { nodeViewProps, NodeViewWrapper } from '@tiptap/vue-3'
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { Avatar, Button, HoverCard, toast, useCall } from 'frappe-ui'

const props = defineProps(nodeViewProps)
const router = useRouter()

const userId = computed(() => props.node.attrs.id)
const label = computed(() => props.node.attrs.label || userId.value)

// The email (userId) is already known from the mention's own attrs and shows
// immediately; only name/avatar need this fetch, cached per-user so hovering
// the same person's mention twice doesn't refire it.
const profile = useCall({
  url: '/api/v2/method/my_new_app.api.get_profile',
  params: () => ({ user: userId.value }),
  // A plain string, not a getter — cacheKey isn't unwrapped reactively, but
  // that's fine: userId is fixed for this NodeView instance's whole lifetime.
  cacheKey: `mention-profile-${userId.value}`,
})

const startDm = useCall({
  url: '/api/v2/method/my_new_app.chat.start_dm',
  method: 'POST',
  immediate: false,
  onSuccess: (data) => {
    router.push({ name: 'Messages', params: { conversationId: data.conversation } })
  },
  onError: (err) => toast.error(err.message),
})

function messageThisPerson() {
  startDm.submit({ other_user: userId.value })
}
</script>
