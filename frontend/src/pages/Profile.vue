<template>
  <PageHeader v-if="!isMobile">
    <Breadcrumbs :items="breadcrumbItems" />
    <Button variant="solid" theme="gray" icon-left="lucide-plus" label="New Post" route="/write" />
  </PageHeader>
  <ScrollArea class="h-full">
    <!-- max-w is 700px of actual Figma content plus 2*20px for the sm:px-5
         gutter this app's pages all share - the gutter isn't part of the
         700px Figma spans, so it has to be added on top rather than eaten
         out of it. -->
    <div class="mx-auto max-w-[740px] px-4 py-6 sm:px-5 sm:py-8">
      <LoadingText v-if="profile.loading && !profile.data" :lines="6" />

      <template v-else-if="profile.data">
        <div class="flex items-start gap-4 sm:gap-8">
          <div
            class="flex size-20 shrink-0 items-center justify-center overflow-hidden rounded-full bg-surface-gray-2 sm:size-25"
          >
            <img
              v-if="profile.data.user_image && !avatarImageError"
              :src="profile.data.user_image"
              :alt="profile.data.full_name"
              class="h-full w-full object-cover"
              @error="avatarImageError = true"
            />
            <span v-else class="text-[2rem] font-medium uppercase text-ink-gray-5 sm:text-[2.5rem]">
              {{ profile.data.full_name?.[0] }}
            </span>
          </div>
          <div class="min-w-0 flex-1">
            <!-- Buttons live on the name's own row (not the whole avatar+headline
                 block), so they only compete for width with the name - the
                 headline below stays free to use the column's full width. -->
            <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <h1 class="truncate text-3xl-semibold text-ink-gray-8 sm:text-7xl-semibold sm:tracking-[0.015em]">{{ profile.data.full_name }}</h1>
              <div class="flex items-center gap-2">
                <template v-if="isOwnProfile">
                  <Button variant="outline" label="Edit" @click="openEditHeader" />
                </template>
                <template v-else>
                  <Button
                    :variant="followingByMe ? 'subtle' : followPending ? 'outline' : 'solid'"
                    theme="gray"
                    :label="followLabel"
                    @click="handleFollowClick"
                  />
                </template>
                <Button variant="outline" icon="lucide-share-2" @click="copyLink" />
              </div>
            </div>
            <div class="mt-1 flex flex-wrap items-center gap-1.5 text-sm text-ink-gray-5">
              <span v-if="profile.data.job_title" class="flex items-center gap-1">
                <span class="lucide-briefcase size-4" aria-hidden="true" />
                {{ profile.data.job_title }}<template v-if="profile.data.company"> at {{ profile.data.company }}</template>
              </span>
              <span v-if="profile.data.job_title">·</span>
              <span class="text-base">@{{ profile.data.username }}</span>
            </div>
            <div v-if="profile.data.headline || isOwnProfile" class="mt-1 flex items-start gap-1.5">
              <p
                class="text-p-lg"
                :class="profile.data.headline ? 'text-ink-gray-6' : 'text-ink-gray-4'"
              >
                {{ profile.data.headline || (isOwnProfile ? 'Add a short headline.' : '') }}
              </p>
            </div>
          </div>
        </div>

        <div class="mt-8 space-y-8">
          <div class="rounded-md border border-outline-gray-1 p-5">
            <div class="flex items-center justify-between pb-4">
              <div class="flex items-center gap-1.5 text-base-medium text-ink-gray-8">
                <span class="lucide-user size-4" aria-hidden="true" />
                Introduction
              </div>
              <Button
                v-if="isOwnProfile"
                variant="ghost"
                theme="gray"
                size="xs"
                class="!text-ink-gray-5 hover:!bg-transparent hover:!text-ink-gray-9 active:!bg-transparent"
                icon="lucide-pencil"
                label="Edit introduction"
                @click="openEditBio"
              />
            </div>
            <template v-if="profile.data.bio">
              <p class="text-p-base text-ink-gray-6" :class="introExpanded ? '' : 'line-clamp-3'">
                {{ profile.data.bio }}
              </p>
              <Button
                v-if="bioNeedsTruncation"
                variant="ghost"
                theme="gray"
                size="sm"
                class="mt-1 w-full justify-end !text-ink-gray-5 hover:!bg-transparent hover:!text-ink-gray-8 hover:!underline active:!bg-transparent"
                :label="introExpanded ? 'see less' : '...see more'"
                @click="introExpanded = !introExpanded"
              />
            </template>
            <p v-else class="text-p-base text-ink-gray-5">
              {{ isOwnProfile ? 'Write about yourself.' : '' }}
            </p>
          </div>

          <div>
            <div class="rounded-md border border-outline-gray-1 p-5">
              <div class="flex items-center gap-1.5 pb-4 text-base-medium text-ink-gray-8">
                <span class="lucide-notebook-pen size-4" aria-hidden="true" />
                Posts
              </div>

              <div v-if="displayedPosts.length" class="divide-y divide-outline-gray-1">
                <router-link
                  v-for="post in displayedPosts"
                  :key="post.name"
                  :to="{ name: 'PostDetail', params: { postId: post.name } }"
                  class="flex items-stretch justify-between gap-4 py-5 first:pt-0 last:pb-0"
                >
                  <div class="flex min-w-0 flex-1 flex-col justify-between">
                    <div>
                      <div class="text-p-base-semibold text-ink-gray-8">{{ post.display_title || post.title || 'Untitled' }}</div>
                      <p class="mt-1 line-clamp-2 text-p-base text-ink-gray-6">{{ post.excerpt || excerpt(post.content, 140) }}</p>
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
              <p v-else class="text-base text-ink-gray-5">
                <template v-if="isOwnProfile">
                  You haven't published anything yet.
                  <router-link to="/write" class="text-base-medium text-ink-gray-8 underline">
                    Write your first blog.
                  </router-link>
                </template>
                <template v-else>No posts yet.</template>
              </p>
            </div>

            <div v-if="showPostsToggle" class="mt-3 flex justify-center">
              <Button
                variant="ghost"
                theme="gray"
                size="sm"
                class="!text-[rgb(113,113,122)] hover:!bg-transparent hover:!text-ink-gray-8 active:!bg-transparent"
                :loading="recentPosts.loading"
                loading-text="Loading..."
                :label="postsExpanded ? 'View less' : 'View all posts'"
                @click="togglePosts"
              />
            </div>
          </div>

          <div>
            <div class="rounded-md border border-outline-gray-1 p-5">
              <div class="flex items-center justify-between pb-4">
                <div class="flex items-center gap-1.5 text-base-medium text-ink-gray-8">
                  <span class="lucide-briefcase size-4" aria-hidden="true" />
                  Work History
                </div>
                <Button
                  v-if="isOwnProfile"
                  variant="ghost"
                  theme="gray"
                  size="xs"
                  class="!text-ink-gray-5 hover:!bg-transparent hover:!text-ink-gray-9 active:!bg-transparent"
                  icon="lucide-plus"
                  label="Add work experience"
                  @click="openAddWork"
                />
              </div>
              <p v-if="!profile.data.work.length" class="text-base text-ink-gray-5">
                {{ isOwnProfile ? 'Add your work experience.' : 'No work history added yet.' }}
              </p>
              <div v-else class="divide-y divide-outline-gray-1">
                <div
                  v-for="job in profile.data.work.slice(0, workLimit)"
                  :key="job.name"
                  class="flex items-start justify-between gap-3 py-5 first:pt-0 last:pb-0"
                >
                  <div>
                    <div class="text-p-base-semibold text-ink-gray-8">{{ job.company }}</div>
                    <!-- Plain inline flow, not flex-wrap: flex-wrap only wraps
                         whole items as opaque boxes, so once the title alone
                         is long enough to wrap onto two lines by itself, the
                         date range gets pushed to a new flex line even when
                         there's visibly leftover room on the title's second
                         line — inline spans wrap word-by-word like normal
                         text, filling that room instead. -->
                    <div class="mt-1 text-p-base text-ink-gray-8">
                      <span v-if="job.title">{{ job.title }}</span>
                      <span v-if="job.title && (job.start_date || job.end_date)" class="text-ink-gray-4"> · </span>
                      <span v-if="job.start_date || job.end_date" class="text-sm text-ink-gray-5">
                        {{ formatMonthYear(job.start_date) }} — {{ job.end_date ? formatMonthYear(job.end_date) : 'Present' }}
                      </span>
                    </div>
                    <p v-if="job.description" class="mt-1 text-p-sm text-ink-gray-6">{{ job.description }}</p>
                  </div>
                  <Button
                    v-if="isOwnProfile"
                    variant="ghost"
                    theme="gray"
                    size="xs"
                    class="shrink-0 !text-ink-gray-4 hover:!bg-transparent hover:!text-ink-gray-8 active:!bg-transparent"
                    icon="lucide-pencil"
                    :label="`Edit ${job.company}`"
                    @click="openEditWork(job)"
                  />
                </div>
              </div>
            </div>

            <div v-if="profile.data.work.length > workLimit" class="mt-3 flex justify-center">
              <Button
                variant="ghost"
                theme="gray"
                size="sm"
                class="!text-[rgb(113,113,122)] hover:!bg-transparent hover:!text-ink-gray-8 active:!bg-transparent"
                label="Show all History"
                @click="workLimit = profile.data.work.length"
              />
            </div>
          </div>

          <div>
            <div class="rounded-md border border-outline-gray-1 p-5">
              <div class="flex items-center justify-between pb-4">
                <div class="flex items-center gap-1.5 text-base-medium text-ink-gray-8">
                  <span class="lucide-graduation-cap size-4" aria-hidden="true" />
                  Education
                </div>
                <Button
                  v-if="isOwnProfile"
                  variant="ghost"
                  theme="gray"
                  size="xs"
                  class="!text-ink-gray-5 hover:!bg-transparent hover:!text-ink-gray-9 active:!bg-transparent"
                  icon="lucide-plus"
                  label="Add education"
                  @click="openAddEducation"
                />
              </div>
              <p v-if="!profile.data.education.length" class="text-base text-ink-gray-5">
                {{ isOwnProfile ? 'Add your education.' : 'No education added yet.' }}
              </p>
              <div v-else class="divide-y divide-outline-gray-1">
                <div
                  v-for="edu in profile.data.education.slice(0, educationLimit)"
                  :key="edu.name"
                  class="flex items-start justify-between gap-3 py-5 first:pt-0 last:pb-0"
                >
                  <div>
                    <div class="text-p-base-semibold text-ink-gray-8">{{ edu.school }}</div>
                    <!-- Plain inline flow, not flex-wrap: flex-wrap only wraps
                         whole items as opaque boxes, so once degree+field
                         alone is long enough to wrap onto two lines by
                         itself, the date range gets pushed to a new flex line
                         even when there's visibly leftover room on that
                         second line — inline spans wrap word-by-word like
                         normal text, filling that room instead. -->
                    <div
                      v-if="edu.degree || edu.field_of_study || edu.start_year || edu.end_year"
                      class="mt-1 text-p-base text-ink-gray-7"
                    >
                      <span v-if="edu.degree || edu.field_of_study">
                        {{ edu.degree }}<template v-if="edu.degree && edu.field_of_study">, </template>{{ edu.field_of_study }}
                      </span>
                      <span
                        v-if="(edu.degree || edu.field_of_study) && (edu.start_year || edu.end_year)"
                        class="text-ink-gray-4"
                        > · </span
                      >
                      <span v-if="edu.start_year || edu.end_year" class="text-sm text-ink-gray-5">
                        {{ formatMonthYear(edu.start_year) }} — {{ edu.end_year ? formatMonthYear(edu.end_year) : 'Present' }}
                      </span>
                    </div>
                  </div>
                  <Button
                    v-if="isOwnProfile"
                    variant="ghost"
                    theme="gray"
                    size="xs"
                    class="shrink-0 !text-ink-gray-4 hover:!bg-transparent hover:!text-ink-gray-8 active:!bg-transparent"
                    icon="lucide-pencil"
                    :label="`Edit ${edu.school}`"
                    @click="openEditEducation(edu)"
                  />
                </div>
              </div>
            </div>

            <div v-if="profile.data.education.length > educationLimit" class="mt-3 flex justify-center">
              <Button
                variant="ghost"
                theme="gray"
                size="sm"
                class="!text-[rgb(113,113,122)] hover:!bg-transparent hover:!text-ink-gray-8 active:!bg-transparent"
                label="Show all Education"
                @click="educationLimit = profile.data.education.length"
              />
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

// Own profile keeps the generic "Profile" crumb; someone else's names them
// directly, reached via Explore - matching how ProfilePosts.vue already
// breadcrumbs into a specific person.
const breadcrumbItems = computed(() => {
  if (isOwnProfile.value) return [{ label: APP_NAME, route: '/' }, { label: 'Profile' }]
  return [
    { label: APP_NAME, route: '/' },
    { label: 'Explore', route: '/' },
    { label: profile.data?.full_name || 'Profile' },
  ]
})

// Follow state needs to flip the instant it's clicked, before the server
// confirms — but profile.data is useCall's read-only computed, so this lives
// in its own local refs (same pattern as PostDetail.vue's like/save/follow),
// kept in sync with profile.data whenever a real fetch lands.
const followingByMe = ref(false)
const followPending = ref(false)
watch(
  () => profile.data,
  (data) => {
    if (!data) return
    followingByMe.value = !!data.following_by_me
    followPending.value = !!data.follow_pending
  },
  { immediate: true },
)

// postsLimit starts at a small page (3); "View all posts" bumps it to 0
// (list_profile_posts/frappe.db.get_all treat a falsy limit as "no limit")
// so the full list is fetched once and cached — collapsing back via "View
// less" is then a pure client-side slice, no refetch needed to re-expand.
const postsLimit = ref(3)
const postsExpanded = ref(false)
watch(targetUser, () => {
  postsLimit.value = 3
  postsExpanded.value = false
})
const recentPosts = useCall({
  url: '/api/v2/method/my_new_app.api.list_profile_posts',
  params: () => ({ user: targetUser.value, limit: postsLimit.value }),
  refetch: true,
})
const displayedPosts = computed(() => {
  if (!recentPosts.data) return []
  return postsExpanded.value ? recentPosts.data : recentPosts.data.slice(0, 3)
})
// Once expanded, postsLimit is 0 (the true total is known) and stays 0 -
// collapsing/re-expanding after that never refetches. Before the first
// expand, "exactly a full page of 3 came back" is the only signal that more
// might exist, same heuristic Work History/Education already rely on.
const showPostsToggle = computed(() => {
  const data = recentPosts.data
  if (!data) return false
  return postsLimit.value === 0 ? data.length > 3 : data.length === postsLimit.value
})
function togglePosts() {
  if (postsExpanded.value) {
    postsExpanded.value = false
    return
  }
  postsExpanded.value = true
  postsLimit.value = 0
}

const introExpanded = ref(false)
const bioNeedsTruncation = computed(() => (profile.data?.bio || '').length > 220)

// Work/education are already fully loaded in one shot by get_profile (unlike
// Posts, which paginates server-side) - "Show all" just lifts a client-side
// cap rather than triggering another request.
const workLimit = ref(3)
const educationLimit = ref(3)

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
})

const unfollowUser = useCall({
  url: '/api/v2/method/my_new_app.follow.unfollow_user',
  method: 'POST',
  immediate: false,
})

const followLabel = computed(() => {
  if (followingByMe.value) return 'Following'
  if (followPending.value) return 'Requested'
  return 'Follow'
})

function handleFollowClick() {
  const wasFollowing = followingByMe.value
  const wasPending = followPending.value

  if (wasFollowing || wasPending) {
    followingByMe.value = false
    followPending.value = false
    unfollowUser.submit({ user: targetUser.value }).then((result) => {
      if (!result) {
        followingByMe.value = wasFollowing
        followPending.value = wasPending
      }
    })
  } else {
    // Only a private account's follow lands as "requested" — optimistically
    // guessing that unconditionally made a public account's button flash
    // "Requested" for a moment before the real "following" response landed.
    if (profile.data?.is_private) {
      followPending.value = true
    } else {
      followingByMe.value = true
    }
    followUser.submit({ user: targetUser.value }).then((result) => {
      if (result) {
        followingByMe.value = result.status === 'following'
        followPending.value = result.status === 'requested'
        if (result.status === 'requested') toast.info('Follow request sent')
      } else {
        followingByMe.value = false
        followPending.value = false
      }
    })
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
    ],
    onConfirm: ({ values, close }) => {
      updateProfile.submit(values)
      close()
    },
  })
}

function openEditBio() {
  dialog.prompt({
    title: 'Edit introduction',
    fields: [{ name: 'bio', label: 'Introduction', type: 'textarea', defaultValue: profile.data.bio }],
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
