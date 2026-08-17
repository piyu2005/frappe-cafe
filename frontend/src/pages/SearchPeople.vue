<template>
  <PageHeader v-if="!isMobile">
    <Breadcrumbs
      :items="
        inviteMode
          ? [{ label: APP_NAME, route: '/' }, { label: pubTitle, route: `/publications/${route.query.pub}` }, { label: 'Invite' }]
          : [{ label: APP_NAME, route: '/' }, { label: 'Search' }]
      "
    />
    <Button variant="solid" theme="gray" icon-left="lucide-plus" label="New Post" route="/write" />
  </PageHeader>
  <ScrollArea class="h-full">
    <div class="mx-auto max-w-[760px] px-4 py-6 sm:px-5 sm:py-8">
      <h1 class="text-3xl font-semibold text-ink-gray-9">
        {{ inviteMode ? `Invite people to ${pubTitle}` : `Writers at ${APP_NAME}` }}
      </h1>

      <TextInput v-model="query" class="mt-5" placeholder="Search" size="lg">
        <template #prefix>
          <span class="lucide-search size-4 text-ink-gray-5" aria-hidden="true" />
        </template>
      </TextInput>

      <LoadingText v-if="people.loading && !people.data" class="mt-6" :lines="4" />

      <div v-else class="mt-4 space-y-1">
        <template v-for="person in peopleData" :key="person.name">
          <!-- Invite mode: clicking a row selects them in place (checkmark +
               role picker + send button) instead of navigating away — same
               shape as a normal search result until you act on it. -->
          <div v-if="inviteMode && selected?.name === person.name" class="rounded-md border border-outline-gray-1 px-3 py-3">
            <div class="flex items-center gap-3">
              <Avatar :image="person.user_image" :label="person.full_name" size="md" />
              <div class="min-w-0 flex-1">
                <div class="text-base text-ink-gray-8">{{ person.full_name }}</div>
                <div v-if="person.username" class="text-sm text-ink-gray-5">@{{ person.username }}</div>
              </div>
              <span class="lucide-check size-4 shrink-0 text-ink-gray-7" aria-hidden="true" />
              <button
                type="button"
                class="flex size-6 shrink-0 items-center justify-center rounded text-ink-gray-5 hover:bg-surface-gray-2 hover:text-ink-gray-8"
                @click="selected = null"
              >
                <span class="lucide-x size-3.5" aria-hidden="true" />
              </button>
            </div>
            <FormControl
              v-model="role"
              class="mt-3"
              type="select"
              label="Select Role"
              :options="[
                { label: 'Member', value: 'Member' },
                { label: 'Editor', value: 'Editor' },
              ]"
            />
            <Button
              class="mt-3 w-full"
              variant="solid"
              theme="gray"
              label="Send invitation"
              :loading="inviteCall.loading"
              @click="sendInvite(person)"
            />
          </div>

          <button
            v-else-if="inviteMode"
            type="button"
            class="flex w-full items-center gap-3 rounded px-2 py-2 text-left hover:bg-surface-gray-1"
            @click="selectPerson(person)"
          >
            <Avatar :image="person.user_image" :label="person.full_name" size="md" />
            <div class="min-w-0 flex-1">
              <span class="text-base text-ink-gray-8">{{ person.full_name }}</span>
              <span v-if="person.username" class="ml-1.5 text-sm text-ink-gray-5">@{{ person.username }}</span>
            </div>
          </button>

          <router-link
            v-else
            :to="{ name: 'Profile', params: { userId: person.name } }"
            class="flex items-center gap-3 rounded px-2 py-2 hover:bg-surface-gray-1"
          >
            <Avatar :image="person.user_image" :label="person.full_name" size="md" />
            <span class="text-base text-ink-gray-8">{{ person.full_name }}</span>
          </router-link>
        </template>

        <p v-if="people.data && peopleData.length === 0" class="py-10 text-center text-p-base text-ink-gray-6">
          {{ inviteMode ? 'No people found.' : 'No writers found.' }}
        </p>
      </div>
    </div>
  </ScrollArea>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import {
  Avatar,
  Breadcrumbs,
  Button,
  FormControl,
  LoadingText,
  PageHeader,
  ScrollArea,
  TextInput,
  toast,
  useCall,
} from 'frappe-ui'
import { APP_NAME } from '@/utils/appName'
import { useIsMobile } from '@/composables/useIsMobile'

const isMobile = useIsMobile()

const route = useRoute()

const inviteMode = computed(() => Boolean(route.query.pub))

const query = ref('')
const selected = ref(null)
const role = ref('Member')

// useCall's `url` is unref'd, not invoked — needs to be a ref/computed, not
// a plain function, to react to inviteMode changing.
const searchUrl = computed(() =>
  inviteMode.value
    ? '/api/v2/method/my_new_app.chat.search_people_to_message'
    : '/api/v2/method/my_new_app.api.list_people',
)

const people = useCall({
  url: searchUrl,
  params: () => ({ query: query.value }),
  refetch: true,
})

const pub = useCall({
  url: '/api/v2/method/my_new_app.api.get_publication',
  params: () => ({ handle: route.query.pub }),
  immediate: false,
})
const pubMembers = useCall({
  url: '/api/v2/method/my_new_app.api.list_publication_members',
  params: () => ({ publication: route.query.pub }),
  immediate: false,
})
watch(
  inviteMode,
  (on) => {
    if (on) {
      pub.reload()
      pubMembers.reload()
    }
  },
  { immediate: true },
)
const pubTitle = computed(() => pub.data?.title || 'Publication')

// Already a member, or already has a pending invite — leave them out of
// invite-mode results entirely rather than letting the request 404 as a
// no-op.
const excludedUserIds = computed(() => {
  if (!inviteMode.value || !pubMembers.data) return new Set()
  const memberIds = [...pubMembers.data.editors, ...pubMembers.data.members].map((m) => m.user)
  const invitedIds = pubMembers.data.pending_invites.map((p) => p.invited_user)
  return new Set([...memberIds, ...invitedIds])
})

const peopleData = computed(() => (people.data || []).filter((p) => !excludedUserIds.value.has(p.name)))

function selectPerson(person) {
  selected.value = person
  role.value = 'Member'
}

const inviteCall = useCall({
  url: '/api/v2/method/my_new_app.api.invite_to_publication',
  method: 'POST',
  immediate: false,
  onSuccess: () => {
    toast.success('Invitation sent')
    selected.value = null
    query.value = ''
    pubMembers.reload()
  },
  onError: (err) => toast.error(err.message),
})

function sendInvite(person) {
  inviteCall.submit({ publication: route.query.pub, user: person.name, role: role.value })
}
</script>
