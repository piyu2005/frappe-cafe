<template>
  <PageHeader v-if="!isMobile">
    <Breadcrumbs :items="[{ label: APP_NAME, route: '/' }, { label: 'Profile' }]" />
    <Button variant="solid" theme="gray" icon-left="lucide-plus" label="New Post" route="/write" />
  </PageHeader>
  <ScrollArea class="h-full">
    <div class="mx-auto max-w-[760px] px-4 py-6 sm:px-5 sm:py-8">
      <LoadingText v-if="profile.loading && !profile.data" :lines="6" />

      <template v-else-if="profile.data">
        <div class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div class="flex items-center gap-4">
            <div
              class="flex size-20 shrink-0 items-center justify-center overflow-hidden rounded-full bg-surface-gray-2 sm:size-28"
            >
              <img
                v-if="profile.data.user_image && !avatarImageError"
                :src="profile.data.user_image"
                :alt="profile.data.full_name"
                class="h-full w-full object-cover"
                @error="avatarImageError = true"
              />
              <span v-else class="text-[2rem] font-medium uppercase text-ink-gray-5 sm:text-[2.75rem]">
                {{ profile.data.full_name?.[0] }}
              </span>
            </div>
            <div class="min-w-0">
              <div class="flex items-center gap-1.5">
                <h1 class="truncate text-3xl font-semibold text-ink-gray-9 sm:text-6xl">{{ profile.data.full_name }}</h1>
              </div>
              <div class="mt-1 flex flex-wrap items-center gap-1.5 text-sm text-ink-gray-5">
                <span v-if="profile.data.job_title" class="flex items-center gap-1">
                  <span class="lucide-briefcase size-3.5" aria-hidden="true" />
                  {{ profile.data.job_title }}<template v-if="profile.data.company"> at {{ profile.data.company }}</template>
                </span>
                <span v-if="profile.data.job_title">·</span>
                <span>@{{ profile.data.username }}</span>
              </div>
              <div v-if="profile.data.headline || isOwnProfile" class="mt-1 flex items-start gap-1.5">
                <p
                  class="text-p-sm"
                  :class="profile.data.headline ? 'text-ink-gray-6' : 'text-ink-gray-4'"
                >
                  {{ profile.data.headline || (isOwnProfile ? 'Add a short headline.' : '') }}
                </p>
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
            <div class="flex items-center justify-between pb-3">
              <div class="flex items-center gap-2 text-lg-semibold text-ink-gray-9">
                <span class="lucide-user size-5" aria-hidden="true" />
                Introduction
              </div>
            </div>
            <template v-if="profile.data.bio">
              <p class="mt-2 text-p-sm text-ink-gray-7" :class="introExpanded ? '' : 'line-clamp-3'">
                {{ profile.data.bio }}
              </p>
              <button
                v-if="bioNeedsTruncation"
                class="mt-1 block w-full text-right text-p-sm text-ink-gray-5 hover:text-ink-gray-8 hover:underline"
                @click="introExpanded = !introExpanded"
              >
                {{ introExpanded ? 'see less' : '...see more' }}
              </button>
            </template>
            <p v-else class="mt-2 text-p-sm text-ink-gray-5">
              {{ isOwnProfile ? 'Write about yourself.' : '' }}
            </p>
          </div>

          <div>
            <div class="rounded-md border border-outline-gray-1 p-4">
              <div class="flex items-center gap-2 pb-3 text-lg-semibold text-ink-gray-9">
                <span class="lucide-notebook-pen size-5" aria-hidden="true" />
                Posts
              </div>

              <div v-if="recentPosts.data && recentPosts.data.length" class="mt-2 divide-y divide-outline-gray-1">
                <router-link
                  v-for="post in recentPosts.data"
                  :key="post.name"
                  :to="{ name: 'PostDetail', params: { postId: post.name } }"
                  class="flex items-stretch justify-between gap-4 py-5 first:pt-0 last:pb-0"
                >
                  <div class="flex min-w-0 flex-1 flex-col justify-between">
                    <div>
                      <div class="text-lg-semibold text-ink-gray-9">{{ post.display_title || post.title || 'Untitled' }}</div>
                      <p class="mt-1 line-clamp-2 text-p-sm text-ink-gray-6">{{ post.excerpt || excerpt(post.content, 140) }}</p>
                    </div>
                    <div class="mt-2 text-xs text-ink-gray-5">
                      {{ formatDate(post.creation) }} · {{ readTime(post.content) }} min read ·
                      {{ post.comment_count }} comment{{ post.comment_count === 1 ? '' : 's' }}
                    </div>
                  </div>
                  <img
                    v-if="thumbnailFor(post)"
                    :src="thumbnailFor(post)"
                    class="h-20 w-24 shrink-0 rounded-md object-cover"
                  />
                </router-link>
              </div>
              <p v-else class="mt-2 text-p-sm text-ink-gray-5">
                <template v-if="isOwnProfile">
                  You haven't published anything yet.
                  <router-link to="/write" class="font-medium text-ink-gray-9 underline">
                    Write your first blog.
                  </router-link>
                </template>
                <template v-else>No posts yet.</template>
              </p>
            </div>

            <button
              v-if="recentPosts.data && recentPosts.data.length === postsLimit"
              class="mt-2 block w-full text-center text-sm text-ink-gray-6 hover:text-ink-gray-9 hover:underline"
              :disabled="recentPosts.loading"
              @click="postsLimit += 10"
            >
              {{ recentPosts.loading ? 'Loading...' : 'View more posts' }}
            </button>
          </div>

          <div class="rounded-md border border-outline-gray-1 p-4">
            <div class="flex items-center justify-between pb-3">
              <div class="flex items-center gap-2 text-lg-semibold text-ink-gray-9">
                <span class="lucide-briefcase size-5" aria-hidden="true" />
                Work History
              </div>
              <button v-if="isOwnProfile" class="text-ink-gray-5 hover:text-ink-gray-9" @click="openAddWork">
                <span class="lucide-plus size-4" aria-hidden="true" />
              </button>
            </div>
            <p v-if="!profile.data.work.length" class="mt-2 text-p-sm text-ink-gray-5">
              {{ isOwnProfile ? 'Add your work experience.' : 'No work history added yet.' }}
            </p>
            <div v-else class="mt-2 divide-y divide-outline-gray-1">
              <div
                v-for="job in profile.data.work"
                :key="job.name"
                class="flex items-start justify-between gap-3 py-5 first:pt-0 last:pb-0"
              >
                <div>
                  <div class="text-base-semibold text-ink-gray-9">{{ job.company }}</div>
                  <!-- Plain inline flow, not flex-wrap: flex-wrap only wraps
                       whole items as opaque boxes, so once the title alone
                       is long enough to wrap onto two lines by itself, the
                       date range gets pushed to a new flex line even when
                       there's visibly leftover room on the title's second
                       line — inline spans wrap word-by-word like normal
                       text, filling that room instead. -->
                  <div class="mt-1 text-base text-ink-gray-8">
                    <span v-if="job.title">{{ job.title }}</span>
                    <span v-if="job.title && (job.start_date || job.end_date)" class="text-ink-gray-4"> · </span>
                    <span v-if="job.start_date || job.end_date">
                      {{ formatMonthYear(job.start_date) }} — {{ job.end_date ? formatMonthYear(job.end_date) : 'Present' }}
                    </span>
                  </div>
                  <p v-if="job.description" class="mt-1 text-p-sm text-ink-gray-5">{{ job.description }}</p>
                </div>
                <button
                  v-if="isOwnProfile"
                  class="shrink-0 text-ink-gray-4 hover:text-ink-gray-8"
                  @click="openEditWork(job)"
                >
                  <span class="lucide-pencil size-3.5" aria-hidden="true" />
                </button>
              </div>
            </div>
          </div>

          <div class="!mt-6 rounded-md border border-outline-gray-1 p-4">
            <div class="flex items-center justify-between pb-3">
              <div class="flex items-center gap-2 text-lg-semibold text-ink-gray-9">
                <span class="lucide-graduation-cap size-5" aria-hidden="true" />
                Education
              </div>
              <button v-if="isOwnProfile" class="text-ink-gray-5 hover:text-ink-gray-9" @click="openAddEducation">
                <span class="lucide-plus size-4" aria-hidden="true" />
              </button>
            </div>
            <p v-if="!profile.data.education.length" class="mt-2 text-p-sm text-ink-gray-5">
              {{ isOwnProfile ? 'Add your education.' : 'No education added yet.' }}
            </p>
            <div v-else class="mt-2 divide-y divide-outline-gray-1">
              <div
                v-for="edu in profile.data.education"
                :key="edu.name"
                class="flex items-start justify-between gap-3 py-5 first:pt-0 last:pb-0"
              >
                <div>
                  <div class="text-base-semibold text-ink-gray-9">{{ edu.school }}</div>
                  <!-- Plain inline flow, not flex-wrap: flex-wrap only wraps
                       whole items as opaque boxes, so once degree+field
                       alone is long enough to wrap onto two lines by
                       itself, the date range gets pushed to a new flex line
                       even when there's visibly leftover room on that
                       second line — inline spans wrap word-by-word like
                       normal text, filling that room instead. -->
                  <div
                    v-if="edu.degree || edu.field_of_study || edu.start_year || edu.end_year"
                    class="mt-1 text-base text-ink-gray-8"
                  >
                    <span v-if="edu.degree || edu.field_of_study">
                      {{ edu.degree }}<template v-if="edu.degree && edu.field_of_study">, </template>{{ edu.field_of_study }}
                    </span>
                    <span
                      v-if="(edu.degree || edu.field_of_study) && (edu.start_year || edu.end_year)"
                      class="text-ink-gray-4"
                      > · </span
                    >
                    <span v-if="edu.start_year || edu.end_year">
                      {{ formatMonthYear(edu.start_year) }} — {{ edu.end_year ? formatMonthYear(edu.end_year) : 'Present' }}
                    </span>
                  </div>
                </div>
                <button
                  v-if="isOwnProfile"
                  class="shrink-0 text-ink-gray-4 hover:text-ink-gray-8"
                  @click="openEditEducation(edu)"
                >
                  <span class="lucide-pencil size-3.5" aria-hidden="true" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </template>

      <Dialog
        v-model="editWorkOpen"
        :title="editWorkForm.name ? 'Edit work experience' : 'Add work experience'"
        size="md"
      >
        <template #default>
          <div class="space-y-4">
            <FormControl v-model="editWorkForm.company" label="Company" required />
            <FormControl v-model="editWorkForm.title" label="Title" />
            <FormControl v-model="editWorkForm.start_date" type="date" label="Start date" />
            <FormControl v-model="editWorkForm.end_date" type="date" label="End date" />
            <FormControl v-model="editWorkForm.description" type="textarea" label="Description" />
          </div>
        </template>
        <template #actions>
          <div class="flex items-center justify-between">
            <Button v-if="editWorkForm.name" variant="ghost" theme="red" label="Delete" @click="deleteWorkFromDialog" />
            <div v-else />
            <div class="flex gap-2">
              <Button variant="outline" label="Cancel" @click="editWorkOpen = false" />
              <Button
                variant="solid"
                theme="gray"
                label="Save"
                :loading="updateWork.loading || addWork.loading"
                @click="saveWork"
              />
            </div>
          </div>
        </template>
      </Dialog>

      <Dialog
        v-model="editEducationOpen"
        :title="editEducationForm.name ? 'Edit education' : 'Add education'"
        size="md"
      >
        <template #default>
          <div class="space-y-4">
            <FormControl v-model="editEducationForm.school" label="School" required />
            <FormControl v-model="editEducationForm.degree" label="Degree" />
            <FormControl v-model="editEducationForm.field_of_study" label="Field of study" />
            <FormControl v-model="editEducationForm.start_year" type="date" label="Start date" />
            <FormControl v-model="editEducationForm.end_year" type="date" label="End date" />
          </div>
        </template>
        <template #actions>
          <div class="flex items-center justify-between">
            <Button
              v-if="editEducationForm.name"
              variant="ghost"
              theme="red"
              label="Delete"
              @click="deleteEducationFromDialog"
            />
            <div v-else />
            <div class="flex gap-2">
              <Button variant="outline" label="Cancel" @click="editEducationOpen = false" />
              <Button
                variant="solid"
                theme="gray"
                label="Save"
                :loading="updateEducation.loading || addEducation.loading"
                @click="saveEducation"
              />
            </div>
          </div>
        </template>
      </Dialog>
    </div>
  </ScrollArea>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import {
  Breadcrumbs,
  Button,
  Dialog,
  FormControl,
  LoadingText,
  PageHeader,
  ScrollArea,
  dialog,
  toast,
  useCall,
} from 'frappe-ui'
import { session } from '@/data/session'
import { APP_NAME } from '@/utils/appName'
import { useIsMobile } from '@/composables/useIsMobile'

const isMobile = useIsMobile()

const route = useRoute()
const targetUser = computed(() => route.params.userId || session.user)
const isOwnProfile = computed(() => targetUser.value === session.user)
const avatarImageError = ref(false)
watch(targetUser, () => {
  avatarImageError.value = false
})

const profile = useCall({
  url: '/api/v2/method/my_new_app.api.get_profile',
  params: () => ({ user: targetUser.value }),
  refetch: true,
})

const postsLimit = ref(3)
const recentPosts = useCall({
  url: '/api/v2/method/my_new_app.api.list_profile_posts',
  params: () => ({ user: targetUser.value, limit: postsLimit.value }),
  refetch: true,
})

const introExpanded = ref(false)
const bioNeedsTruncation = computed(() => (profile.data?.bio || '').length > 220)

function thumbnailFor(post) {
  if (post.cover_image) return post.cover_image
  if (post.post_type === 'Image') return post.attachment
  return null
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

function readTime(content) {
  const words = stripHtml(content).trim().split(/\s+/).filter(Boolean).length
  return Math.max(1, Math.round(words / 200))
}

function formatDate(value) {
  if (!value) return ''
  return new Date(value).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
}

// Work history dates only ever need month + year, and the three-letter
// abbreviation (Jan, Feb, ...) is what should show — not the full month name.
function formatMonthYear(value) {
  if (!value) return ''
  const date = new Date(value)
  if (isNaN(date)) return value
  return date.toLocaleDateString(undefined, { month: 'short', year: 'numeric' })
}

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
  onSuccess: () => {
    profile.reload()
    editEducationOpen.value = false
  },
})

const updateEducation = useCall({
  url: '/api/v2/method/my_new_app.api.update_education',
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
  onSuccess: () => {
    profile.reload()
    editWorkOpen.value = false
  },
})

const updateWork = useCall({
  url: '/api/v2/method/my_new_app.api.update_work',
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
      { name: 'headline', label: 'Headline', defaultValue: profile.data.headline },
      { name: 'job_title', label: 'Job title', defaultValue: profile.data.job_title },
      { name: 'company', label: 'Company', defaultValue: profile.data.company },
      { name: 'bio', label: 'Introduction', type: 'textarea', defaultValue: profile.data.bio },
    ],
    onConfirm: ({ values, close }) => {
      updateProfile.submit(values)
      close()
    },
  })
}

const editEducationOpen = ref(false)
const editEducationForm = reactive({
  name: '',
  school: '',
  degree: '',
  field_of_study: '',
  start_year: '',
  end_year: '',
})
function openAddEducation() {
  Object.assign(editEducationForm, {
    name: '',
    school: '',
    degree: '',
    field_of_study: '',
    start_year: '',
    end_year: '',
  })
  editEducationOpen.value = true
}

function openEditEducation(edu) {
  Object.assign(editEducationForm, {
    name: edu.name,
    school: edu.school || '',
    degree: edu.degree || '',
    field_of_study: edu.field_of_study || '',
    start_year: edu.start_year || '',
    end_year: edu.end_year || '',
  })
  editEducationOpen.value = true
}

function saveEducation() {
  if (!editEducationForm.school) return
  if (editEducationForm.name) {
    updateEducation.submit({ ...editEducationForm }).then(() => {
      editEducationOpen.value = false
    })
  } else {
    const { name, ...values } = editEducationForm
    addEducation.submit(values)
  }
}

function deleteEducationFromDialog() {
  dialog.danger({
    title: 'Delete education?',
    message: `This will permanently remove "${editEducationForm.school}" from your profile.`,
    onConfirm: () =>
      deleteEducation.submit({ name: editEducationForm.name }).then(() => {
        editEducationOpen.value = false
      }),
  })
}

const editWorkOpen = ref(false)
const editWorkForm = reactive({
  name: '',
  company: '',
  title: '',
  start_date: '',
  end_date: '',
  description: '',
})
function openAddWork() {
  Object.assign(editWorkForm, {
    name: '',
    company: '',
    title: '',
    start_date: '',
    end_date: '',
    description: '',
  })
  editWorkOpen.value = true
}

function openEditWork(job) {
  Object.assign(editWorkForm, {
    name: job.name,
    company: job.company || '',
    title: job.title || '',
    start_date: job.start_date || '',
    end_date: job.end_date || '',
    description: job.description || '',
  })
  editWorkOpen.value = true
}

function saveWork() {
  if (!editWorkForm.company) return
  if (editWorkForm.name) {
    updateWork.submit({ ...editWorkForm }).then(() => {
      editWorkOpen.value = false
    })
  } else {
    const { name, ...values } = editWorkForm
    addWork.submit(values)
  }
}

function deleteWorkFromDialog() {
  dialog.danger({
    title: 'Delete work experience?',
    message: `This will permanently remove "${editWorkForm.company}" from your profile.`,
    onConfirm: () =>
      deleteWork.submit({ name: editWorkForm.name }).then(() => {
        editWorkOpen.value = false
      }),
  })
}

function copyLink() {
  navigator.clipboard.writeText(window.location.href)
  toast.success('Link copied')
}
</script>
