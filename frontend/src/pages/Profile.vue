<template>
  <PageHeader>
    <Breadcrumbs :items="[{ label: APP_NAME, route: '/' }, { label: 'Profile' }]" />
    <Button variant="ghost" icon-left="lucide-pencil" label="Write your story" route="/write" />
  </PageHeader>

  <ScrollArea class="h-[calc(100vh-3rem)]">
    <div class="mx-auto max-w-[760px] px-5 py-8">
      <LoadingText v-if="profile.loading && !profile.data" :lines="6" />

      <template v-else-if="profile.data">
        <div class="flex items-start justify-between">
          <div class="flex items-center gap-4">
            <Avatar :image="profile.data.user_image" :label="profile.data.full_name" size="2xl" />
            <div>
              <h1 class="text-2xl font-semibold text-ink-gray-9">{{ profile.data.full_name }}</h1>
              <div class="mt-1 flex items-center gap-1.5 text-sm text-ink-gray-5">
                <span v-if="profile.data.job_title">
                  {{ profile.data.job_title }}<template v-if="profile.data.company"> at {{ profile.data.company }}</template>
                </span>
                <span v-if="profile.data.job_title">·</span>
                <span>@{{ profile.data.username }}</span>
              </div>
              <div class="mt-1 flex items-center gap-1.5 text-sm text-ink-gray-5">
                <span v-if="profile.data.is_private" class="flex items-center gap-1">
                  <span class="lucide-lock size-3" aria-hidden="true" />
                </span>
                {{ profile.data.follower_count }} follower{{ profile.data.follower_count === 1 ? '' : 's' }}
              </div>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <template v-if="isOwnProfile">
              <Button label="Edit" @click="openEditHeader" />
            </template>
            <template v-else>
              <Button
                :variant="profile.data.following_by_me || profile.data.follow_pending ? 'outline' : 'solid'"
                theme="gray"
                :label="followLabel"
                :loading="followUser.loading || unfollowUser.loading"
                @click="handleFollowClick"
              />
            </template>
            <Button icon="lucide-share-2" @click="copyLink" />
          </div>
        </div>

        <div class="mt-6 space-y-4">
          <div class="rounded-md border border-outline-gray-1 p-4">
            <div class="flex items-center gap-2 text-base-medium text-ink-gray-8">
              <span class="lucide-user size-4" aria-hidden="true" />
              Introduction
            </div>
            <button
              class="mt-2 block w-full text-left text-p-sm"
              :class="profile.data.bio ? 'text-ink-gray-7' : 'text-ink-gray-5'"
              :disabled="!isOwnProfile"
              @click="isOwnProfile && openEditBio()"
            >
              {{ profile.data.bio || (isOwnProfile ? 'Write about yourself.' : '') }}
            </button>
          </div>

          <div class="rounded-md border border-outline-gray-1 p-4">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2 text-base-medium text-ink-gray-8">
                <span class="lucide-pen-line size-4" aria-hidden="true" />
                Posts
              </div>
              <div v-if="isOwnProfile" class="flex items-center gap-1 rounded-md bg-surface-gray-2 p-0.5">
                <button
                  v-for="f in postFilters"
                  :key="f.value"
                  class="rounded px-2 py-1 text-xs"
                  :class="postFilter === f.value ? 'bg-surface-base text-ink-gray-9 shadow-sm' : 'text-ink-gray-5'"
                  @click="postFilter = f.value"
                >
                  {{ f.label }}
                </button>
              </div>
            </div>
            <p v-if="userPosts.data && userPosts.data.length === 0" class="mt-2 text-p-sm text-ink-gray-5">
              <template v-if="isOwnProfile && postFilter === 'Published'">
                You haven't published anything yet.
                <router-link to="/write" class="font-medium text-ink-gray-9 underline">
                  Write your first blog.
                </router-link>
              </template>
              <template v-else-if="isOwnProfile">No {{ postFilter.toLowerCase() }} posts.</template>
              <template v-else>No posts yet.</template>
            </p>
            <div v-else class="mt-2 divide-y divide-outline-gray-1">
              <div
                v-for="post in userPosts.data"
                :key="post.name"
                class="flex items-center gap-2 py-3 first:pt-0 last:pb-0"
              >
                <router-link
                  :to="
                    post.status === 'Published'
                      ? { name: 'PostDetail', params: { postId: post.name } }
                      : { name: 'WritePost', params: { postId: post.name } }
                  "
                  class="block min-w-0 flex-1"
                >
                  <div class="flex items-center gap-2">
                    <div class="truncate text-base-medium text-ink-gray-9">{{ post.title || 'Untitled' }}</div>
                    <Badge
                      v-if="post.status !== 'Published'"
                      :label="post.status"
                      variant="subtle"
                      theme="gray"
                      size="sm"
                    />
                  </div>
                  <p class="mt-1 line-clamp-2 text-p-sm text-ink-gray-6">{{ excerpt(post.content, 140) }}</p>
                  <div class="mt-1 text-xs text-ink-gray-5">{{ formatDate(post.creation) }}</div>
                </router-link>
                <router-link
                  v-if="isOwnProfile"
                  :to="{ name: 'WritePost', params: { postId: post.name } }"
                  class="shrink-0 text-ink-gray-4 hover:text-ink-gray-9"
                >
                  <span class="lucide-pencil size-4" aria-hidden="true" />
                </router-link>
              </div>
            </div>
          </div>

          <div class="rounded-md border border-outline-gray-1 p-4">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2 text-base-medium text-ink-gray-8">
                <span class="lucide-graduation-cap size-4" aria-hidden="true" />
                Education
              </div>
              <button v-if="isOwnProfile" class="text-ink-gray-5 hover:text-ink-gray-9" @click="openAddEducation">
                <span class="lucide-plus size-4" aria-hidden="true" />
              </button>
            </div>
            <p v-if="!profile.data.education.length" class="mt-2 text-p-sm text-ink-gray-5">
              {{ isOwnProfile ? 'Add your education.' : 'No education added yet.' }}
            </p>
            <div v-else class="mt-2 space-y-3">
              <div v-for="edu in profile.data.education" :key="edu.name" class="flex items-start justify-between">
                <div>
                  <div class="text-base-medium text-ink-gray-8">{{ edu.school }}</div>
                  <div class="text-sm text-ink-gray-5">
                    <template v-if="edu.degree">{{ edu.degree }}<template v-if="edu.field_of_study">, {{ edu.field_of_study }}</template></template>
                    <template v-if="edu.start_year || edu.end_year">
                      · {{ edu.start_year }}–{{ edu.end_year }}
                    </template>
                  </div>
                </div>
                <button v-if="isOwnProfile" class="text-ink-gray-4 hover:text-ink-red-6" @click="removeEducation(edu.name)">
                  <span class="lucide-x size-4" aria-hidden="true" />
                </button>
              </div>
            </div>
          </div>

          <div class="rounded-md border border-outline-gray-1 p-4">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2 text-base-medium text-ink-gray-8">
                <span class="lucide-briefcase size-4" aria-hidden="true" />
                Work History
              </div>
              <button v-if="isOwnProfile" class="text-ink-gray-5 hover:text-ink-gray-9" @click="openAddWork">
                <span class="lucide-plus size-4" aria-hidden="true" />
              </button>
            </div>
            <p v-if="!profile.data.work.length" class="mt-2 text-p-sm text-ink-gray-5">
              {{ isOwnProfile ? 'Add your work experience.' : 'No work history added yet.' }}
            </p>
            <div v-else class="mt-2 space-y-3">
              <div v-for="job in profile.data.work" :key="job.name" class="flex items-start justify-between">
                <div>
                  <div class="text-base-medium text-ink-gray-8">
                    {{ job.title }}<template v-if="job.title && job.company"> at </template>{{ job.company }}
                  </div>
                  <div class="text-sm text-ink-gray-5">
                    <template v-if="job.start_date || job.end_date">{{ job.start_date }} – {{ job.end_date || 'Present' }}</template>
                  </div>
                  <p v-if="job.description" class="mt-1 text-p-sm text-ink-gray-6">{{ job.description }}</p>
                </div>
                <button v-if="isOwnProfile" class="text-ink-gray-4 hover:text-ink-red-6" @click="removeWork(job.name)">
                  <span class="lucide-x size-4" aria-hidden="true" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </ScrollArea>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import {
  Avatar,
  Badge,
  Breadcrumbs,
  Button,
  LoadingText,
  PageHeader,
  ScrollArea,
  dialog,
  toast,
  useCall,
  useList,
} from 'frappe-ui'
import { session } from '@/data/session'
import { APP_NAME } from '@/utils/appName'

const route = useRoute()
const targetUser = computed(() => route.params.userId || session.user)
const isOwnProfile = computed(() => targetUser.value === session.user)

const profile = useCall({
  url: '/api/v2/method/my_new_app.api.get_profile',
  params: () => ({ user: targetUser.value }),
  refetch: true,
})

const postFilters = [
  { label: 'Published', value: 'Published' },
  { label: 'Drafts', value: 'Draft' },
  { label: 'Archived', value: 'Archived' },
]
const postFilter = ref('Published')

const userPosts = useList({
  doctype: 'Post',
  fields: ['name', 'title', 'content', 'status', 'creation'],
  filters: () => ({
    author: targetUser.value,
    status: isOwnProfile.value ? postFilter.value : 'Published',
  }),
  orderBy: 'creation desc',
  limit: 20,
  refetch: true,
})

const updateProfile = useCall({
  url: '/api/v2/method/my_new_app.api.update_profile',
  method: 'POST',
  immediate: false,
  onSuccess: () => profile.reload(),
})

const followUser = useCall({
  url: '/api/v2/method/my_new_app.follow.follow_user',
  method: 'POST',
  immediate: false,
  onSuccess: (data) => {
    profile.reload()
    if (data.status === 'requested') toast.info('Follow request sent')
  },
})

const unfollowUser = useCall({
  url: '/api/v2/method/my_new_app.follow.unfollow_user',
  method: 'POST',
  immediate: false,
  onSuccess: () => profile.reload(),
})

const followLabel = computed(() => {
  if (profile.data?.following_by_me) return 'Following'
  if (profile.data?.follow_pending) return 'Requested'
  return 'Follow'
})

function handleFollowClick() {
  if (profile.data.following_by_me || profile.data.follow_pending) {
    unfollowUser.submit({ user: targetUser.value })
  } else {
    followUser.submit({ user: targetUser.value })
  }
}

const addEducation = useCall({
  url: '/api/v2/method/my_new_app.api.add_education',
  method: 'POST',
  immediate: false,
  onSuccess: () => profile.reload(),
})

const deleteEducation = useCall({
  url: '/api/v2/method/my_new_app.api.delete_education',
  method: 'POST',
  immediate: false,
  onSuccess: () => profile.reload(),
})

const addWork = useCall({
  url: '/api/v2/method/my_new_app.api.add_work',
  method: 'POST',
  immediate: false,
  onSuccess: () => profile.reload(),
})

const deleteWork = useCall({
  url: '/api/v2/method/my_new_app.api.delete_work',
  method: 'POST',
  immediate: false,
  onSuccess: () => profile.reload(),
})

function openEditHeader() {
  dialog.prompt({
    title: 'Edit profile',
    fields: [
      { name: 'full_name', label: 'Full name', defaultValue: profile.data.full_name, required: true },
      { name: 'job_title', label: 'Job title', defaultValue: profile.data.job_title },
      { name: 'company', label: 'Company', defaultValue: profile.data.company },
    ],
    onConfirm: ({ values, close }) => {
      updateProfile.submit(values)
      close()
    },
  })
}

function openEditBio() {
  dialog.prompt({
    title: 'Introduction',
    fields: [{ name: 'bio', label: 'About you', type: 'textarea', defaultValue: profile.data.bio }],
    onConfirm: ({ values, close }) => {
      updateProfile.submit(values)
      close()
    },
  })
}

function openAddEducation() {
  dialog.prompt({
    title: 'Add education',
    fields: [
      { name: 'school', label: 'School', required: true },
      { name: 'degree', label: 'Degree' },
      { name: 'field_of_study', label: 'Field of study' },
      { name: 'start_year', label: 'Start year' },
      { name: 'end_year', label: 'End year' },
    ],
    onConfirm: ({ values, close }) => {
      addEducation.submit(values)
      close()
    },
  })
}

function removeEducation(name) {
  deleteEducation.submit({ name })
}

function openAddWork() {
  dialog.prompt({
    title: 'Add work experience',
    fields: [
      { name: 'company', label: 'Company', required: true },
      { name: 'title', label: 'Title' },
      { name: 'start_date', label: 'Start date' },
      { name: 'end_date', label: 'End date' },
      { name: 'description', label: 'Description', type: 'textarea' },
    ],
    onConfirm: ({ values, close }) => {
      addWork.submit(values)
      close()
    },
  })
}

function removeWork(name) {
  deleteWork.submit({ name })
}

function copyLink() {
  navigator.clipboard.writeText(window.location.href)
  toast.success('Link copied')
}

function formatDate(value) {
  if (!value) return ''
  return new Date(value).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

function stripHtml(html) {
  const div = document.createElement('div')
  div.innerHTML = html || ''
  return div.textContent || div.innerText || ''
}

function excerpt(content, length) {
  const text = stripHtml(content).trim()
  return text.length > length ? text.slice(0, length) + '…' : text
}
</script>
