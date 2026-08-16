<template>
  <PageHeader v-if="!isMobile">
    <Breadcrumbs
      :items="[
        { label: APP_NAME, route: '/' },
        { label: pubTitle, route: `/publications/${route.params.handle}` },
        { label: 'Members' },
      ]"
    />
    <Button variant="solid" theme="gray" icon-left="lucide-plus" label="New Post" route="/write" />
  </PageHeader>
  <PageHeaderMobile v-else title="Members">
    <template #left>
      <PageHeaderBackButton :to="`/publications/${route.params.handle}`" />
    </template>
    <template #right>
      <MobileNotificationBell />
    </template>
  </PageHeaderMobile>

  <ScrollArea class="h-[calc(100vh-52px)] md:h-[calc(100vh-3rem)]">
    <div class="mx-auto max-w-[640px] px-5 py-8">
      <div class="mb-6 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <router-link
            :to="`/publications/${route.params.handle}`"
            class="flex size-8 items-center justify-center rounded-full text-ink-gray-6 hover:bg-surface-gray-2"
          >
            <span class="lucide-arrow-left size-4" aria-hidden="true" />
          </router-link>
          <h1 class="text-xl font-semibold text-ink-gray-9">Members from {{ pubTitle }}</h1>
        </div>
        <Button
          v-if="isAdmin"
          variant="subtle"
          theme="gray"
          icon-left="lucide-user-plus"
          label="Invite"
          :route="{ name: 'SearchPeople', query: { pub: route.params.handle } }"
        />
      </div>

      <LoadingText v-if="members.loading && !members.data" :lines="6" />

      <template v-else-if="members.data">
        <div class="mb-6">
          <span class="mb-2 flex items-center gap-1.5 text-sm-medium text-ink-gray-7">
            <span class="lucide-pencil size-3.5" aria-hidden="true" />
            Editors
          </span>
          <div class="divide-y divide-outline-gray-1 rounded-md border border-outline-gray-1">
            <div v-for="m in members.data.editors" :key="m.name" class="flex items-center gap-3 px-3 py-2.5">
              <Avatar :image="m.user_image" :label="m.full_name" size="md" />
              <div class="min-w-0 flex-1">
                <div class="flex items-center gap-1.5">
                  <span class="truncate text-sm-medium text-ink-gray-9">{{ m.full_name }}</span>
                  <Badge v-if="m.user === session.user" variant="subtle" theme="gray" size="sm" label="You" />
                </div>
              </div>
              <Dropdown v-if="isAdmin && m.user !== session.user" :options="memberOptions(m)">
                <Badge
                  class="cursor-pointer"
                  :variant="m.role === 'Admin' ? 'solid' : 'subtle'"
                  :theme="m.role === 'Admin' ? 'green' : 'blue'"
                  size="sm"
                  :label="m.role"
                />
              </Dropdown>
              <Badge v-else :variant="m.role === 'Admin' ? 'solid' : 'subtle'" :theme="m.role === 'Admin' ? 'green' : 'blue'" size="sm" :label="m.role" />
            </div>
          </div>
        </div>

        <div v-if="members.data.members.length" class="mb-6">
          <span class="mb-2 flex items-center gap-1.5 text-sm-medium text-ink-gray-7">
            <span class="lucide-user size-3.5" aria-hidden="true" />
            Members
          </span>
          <div class="divide-y divide-outline-gray-1 rounded-md border border-outline-gray-1">
            <div v-for="m in members.data.members" :key="m.name" class="flex items-center gap-3 px-3 py-2.5">
              <Avatar :image="m.user_image" :label="m.full_name" size="md" />
              <div class="min-w-0 flex-1">
                <div class="flex items-center gap-1.5">
                  <span class="truncate text-sm-medium text-ink-gray-9">{{ m.full_name }}</span>
                  <Badge v-if="m.user === session.user" variant="subtle" theme="gray" size="sm" label="You" />
                </div>
              </div>
              <Dropdown v-if="isAdmin && m.user !== session.user" :options="memberOptions(m)">
                <Badge class="cursor-pointer" variant="subtle" theme="gray" size="sm" label="Member" />
              </Dropdown>
              <Badge v-else variant="subtle" theme="gray" size="sm" label="Member" />
            </div>
          </div>
        </div>

        <div v-if="isAdmin && members.data.pending_invites.length">
          <span class="mb-2 block text-sm-medium text-ink-gray-7">Pending invites</span>
          <div class="divide-y divide-outline-gray-1 rounded-md border border-outline-gray-1">
            <div
              v-for="p in members.data.pending_invites"
              :key="p.name"
              class="flex items-center gap-3 px-3 py-2.5"
            >
              <Avatar :image="p.user_image" :label="p.full_name" size="md" />
              <span class="min-w-0 flex-1 truncate text-sm-medium text-ink-gray-9">{{ p.full_name }}</span>
              <Badge variant="subtle" theme="gray" size="sm" :label="p.role" />
              <Button variant="ghost" size="sm" label="Cancel" @click="cancelInvite(p.name)" />
            </div>
          </div>
        </div>
      </template>
    </div>
  </ScrollArea>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import {
  Avatar,
  Badge,
  Breadcrumbs,
  Button,
  Dropdown,
  LoadingText,
  PageHeader,
  PageHeaderBackButton,
  PageHeaderMobile,
  ScrollArea,
  dialog,
  toast,
  useCall,
} from 'frappe-ui'
import { session } from '@/data/session'
import { APP_NAME } from '@/utils/appName'
import MobileNotificationBell from '@/components/MobileNotificationBell.vue'
import { useIsMobile } from '@/composables/useIsMobile'

const isMobile = useIsMobile()
const route = useRoute()

const pub = useCall({
  url: '/api/v2/method/my_new_app.api.get_publication',
  params: () => ({ handle: route.params.handle }),
})
const pubTitle = computed(() => pub.data?.title || 'Publication')

const members = useCall({
  url: '/api/v2/method/my_new_app.api.list_publication_members',
  params: () => ({ publication: route.params.handle }),
})

const isAdmin = computed(() => members.data?.my_role === 'Admin')

const cancelInviteCall = useCall({
  url: '/api/v2/method/my_new_app.api.cancel_publication_invite',
  method: 'POST',
  immediate: false,
  onSuccess: () => members.reload(),
})

function cancelInvite(name) {
  cancelInviteCall.submit({ name })
}

const removeCall = useCall({
  url: '/api/v2/method/my_new_app.api.remove_publication_member',
  method: 'POST',
  immediate: false,
  onSuccess: () => members.reload(),
  onError: (err) => toast.error(err.message),
})

const roleCall = useCall({
  url: '/api/v2/method/my_new_app.api.set_publication_member_role',
  method: 'POST',
  immediate: false,
  onSuccess: () => members.reload(),
  onError: (err) => toast.error(err.message),
})

function setRole(m, role) {
  roleCall.submit({ publication: route.params.handle, user: m.user, role })
}

function memberOptions(m) {
  const options = []
  if (m.role !== 'Admin') {
    options.push({
      label: 'Make admin',
      icon: 'lucide-shield',
      onClick: () => setRole(m, 'Admin'),
    })
  }
  if (m.role !== 'Editor') {
    options.push({
      label: 'Make editor',
      icon: 'lucide-pencil',
      onClick: () => setRole(m, 'Editor'),
    })
  }
  if (m.role !== 'Member') {
    options.push({
      label: 'Make member',
      icon: 'lucide-user',
      onClick: () => setRole(m, 'Member'),
    })
  }
  options.push({
    label: 'Remove from publication',
    icon: 'lucide-user-minus',
    onClick: () =>
      dialog.confirm({
        title: 'Remove this member?',
        message: `${m.full_name} will be removed from ${pubTitle.value}.`,
        theme: 'red',
        confirmLabel: 'Remove',
        onConfirm: () => removeCall.submit({ publication: route.params.handle, user: m.user }),
      }),
  })
  return options
}
</script>
