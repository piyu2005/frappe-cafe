<template>
  <PageHeader>
    <Breadcrumbs :items="breadcrumbItems" />
    <Button variant="ghost" icon-left="lucide-pencil" label="Write your story" route="/write" />
  </PageHeader>

  <ScrollArea class="h-[calc(100vh-3rem)]">
    <div class="mx-auto max-w-[770px] px-5 py-8">
      <LoadingText v-if="post.loading && !post.data" :lines="8" />

      <div v-else-if="post.error && !post.data" class="flex flex-col items-center gap-3 py-24 text-center">
        <span class="lucide-lock size-8 text-ink-gray-3" aria-hidden="true" />
        <p class="text-p-base text-ink-gray-5">
          This post isn't available. It may be a draft, archived, or removed.
        </p>
      </div>

      <template v-else-if="post.data">
        <h1 class="text-3xl font-semibold text-ink-gray-9">{{ post.data.title }}</h1>

        <div class="mt-4 flex items-center gap-3">
          <Avatar :image="post.data.author_image" :label="post.data.author_name" size="md" />
          <div class="min-w-0 flex-1">
            <router-link
              :to="{ name: 'Profile', params: { userId: post.data.author } }"
              class="text-base-medium text-ink-gray-9 hover:underline"
            >
              {{ post.data.author_name }}
            </router-link>
            <div class="text-sm text-ink-gray-5">
              {{ formatDate(post.data.creation) }} · {{ readTime(post.data.content) }} min read
            </div>
          </div>
          <Button
            v-if="post.data.author !== session.user"
            :variant="post.data.author_following_by_me || post.data.author_follow_pending ? 'outline' : 'solid'"
            theme="gray"
            :label="authorFollowLabel"
            :loading="followUser.loading || unfollowUser.loading"
            @click="handleFollowClick"
          />
          <Button
            icon="lucide-bookmark"
            :variant="post.data.saved_by_me ? 'solid' : 'outline'"
            theme="gray"
            :loading="toggleSave.loading"
            @click="handleSave"
          />
          <Dropdown :options="moreOptions">
            <Button icon="lucide-more-horizontal" />
          </Dropdown>
        </div>

        <img
          v-if="post.data.post_type !== 'Video' && (post.data.cover_image || post.data.attachment)"
          :src="post.data.cover_image || post.data.attachment"
          class="mt-6 w-full rounded-md object-cover"
        />

        <Editor
          class="mt-6"
          :model-value="renderedContent"
          :extensions="readExtensions"
          :editable="false"
        >
          <template #default>
            <EditorContent />
          </template>
        </Editor>

        <div v-if="post.data.tags.length" class="mt-6 flex flex-wrap gap-2">
          <Badge v-for="tag in post.data.tags" :key="tag" :label="tag" variant="subtle" size="lg" />
        </div>

        <div class="mt-8 flex items-center justify-between rounded-md border border-outline-gray-1 p-4">
          <div class="flex items-center gap-3">
            <Avatar :image="post.data.author_image" :label="post.data.author_name" size="lg" />
            <div>
              <div class="text-sm text-ink-gray-5">Written by</div>
              <div class="text-base-medium text-ink-gray-9">{{ post.data.author_name }}</div>
              <p v-if="post.data.author_bio" class="mt-1 max-w-md text-p-sm text-ink-gray-6">
                {{ post.data.author_bio }}
              </p>
            </div>
          </div>
          <Button
            v-if="post.data.author !== session.user"
            :variant="post.data.author_following_by_me || post.data.author_follow_pending ? 'outline' : 'solid'"
            theme="gray"
            :label="authorFollowLabel"
            :loading="followUser.loading || unfollowUser.loading"
            @click="handleFollowClick"
          />
        </div>

        <div class="mt-4 flex items-center justify-between border-y border-outline-gray-1 py-3">
          <div class="flex items-center gap-4">
            <button
              class="flex items-center gap-1.5 text-sm"
              :class="post.data.liked_by_me ? 'text-ink-red-6' : 'text-ink-gray-6'"
              @click="like"
            >
              <span
                :class="post.data.liked_by_me ? 'lucide-heart fill-current' : 'lucide-heart'"
                class="size-4"
                aria-hidden="true"
              />
              {{ post.data.like_count }}
            </button>
            <span class="flex items-center gap-1.5 text-sm text-ink-gray-6">
              <span class="lucide-message-circle size-4" aria-hidden="true" />
              {{ post.data.comment_count }}
            </span>
          </div>
          <div class="flex items-center gap-2">
            <Button icon="lucide-share-2" @click="copyLink" />
            <Button
            icon="lucide-bookmark"
            :variant="post.data.saved_by_me ? 'solid' : 'outline'"
            theme="gray"
            :loading="toggleSave.loading"
            @click="handleSave"
          />
          </div>
        </div>

        <h2 class="mt-6 text-lg-semibold text-ink-gray-9">Responses ({{ post.data.comment_count }})</h2>

        <div class="mt-3">
          <FormControl
            v-model="newComment"
            type="textarea"
            placeholder="What are your thoughts?"
            :rows="3"
          />
          <Button
            class="mt-2"
            variant="solid"
            theme="gray"
            label="Comment"
            :loading="addComment.loading"
            @click="submitComment"
          />
        </div>

        <div class="mt-6 divide-y divide-outline-gray-1">
          <div v-for="c in visibleComments" :key="c.name" class="py-4">
            <div class="flex items-center gap-2">
              <Avatar :image="c.comment_by_image" :label="c.comment_by_name" size="sm" />
              <span class="text-sm-medium text-ink-gray-8">{{ c.comment_by_name }}</span>
              <span class="text-xs text-ink-gray-5">{{ timeAgo(c.creation) }}</span>
            </div>
            <p class="mt-1 pl-8 text-p-sm text-ink-gray-7">{{ c.content }}</p>
            <div class="mt-1 flex items-center gap-3 pl-8 text-xs">
              <button
                class="flex items-center gap-1"
                :class="c.liked_by_me ? 'text-ink-red-6' : 'text-ink-gray-5'"
                @click="toggleCommentLike(c)"
              >
                <span
                  :class="c.liked_by_me ? 'lucide-heart fill-current' : 'lucide-heart'"
                  class="size-3"
                  aria-hidden="true"
                />
                {{ c.like_count }}
              </button>
              <button class="text-ink-gray-5 hover:underline" @click="toast.info('Replies are coming soon')">Reply</button>
            </div>
          </div>
        </div>

        <button
          v-if="commentList.length > visibleCount"
          class="mt-2 w-full text-center text-sm text-ink-gray-6 hover:underline"
          @click="visibleCount += 10"
        >
          Show more comments
        </button>
      </template>
    </div>
  </ScrollArea>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Avatar,
  Badge,
  Breadcrumbs,
  Button,
  Dropdown,
  FormControl,
  LoadingText,
  PageHeader,
  ScrollArea,
  toast,
  useCall,
} from 'frappe-ui'
import { Editor, EditorContent, RichTextKit } from 'frappe-ui/editor'
import { session } from '@/data/session'
import { ensureHtmlContent } from '@/utils/content'
import { APP_NAME } from '@/utils/appName'

const router = useRouter()
const readExtensions = [RichTextKit.configure({ mention: false, tag: false })]

const route = useRoute()
const newComment = ref('')
const visibleCount = ref(5)

const post = useCall({
  url: '/api/v2/method/my_new_app.api.get_post',
  params: () => ({ post_id: route.params.postId }),
  refetch: true,
})

const comments = useCall({
  url: '/api/v2/method/my_new_app.api.list_comments',
  params: () => ({ post: route.params.postId }),
  refetch: true,
})

// useCall's `.data` is a read-only computed — mutating a nested property of an
// array item held there doesn't reliably trigger a re-render. Keep a local
// mutable copy (same pattern as Messages.vue's reaction handling) so liking a
// comment can update its count/heart in place instead of reloading the list.
const commentList = ref([])
watch(
  () => comments.data,
  (val) => {
    commentList.value = val ? [...val] : []
  },
  { immediate: true },
)

const visibleComments = computed(() => commentList.value.slice(0, visibleCount.value))

const renderedContent = computed(() => ensureHtmlContent(post.data?.content))

const breadcrumbItems = computed(() => {
  const items = [
    { label: APP_NAME, route: '/' },
    { label: 'Explore', route: '/' },
  ]
  if (post.data?.author_name) {
    items.push({ label: post.data.author_name, route: `/profile/${post.data.author}` })
  }
  items.push({ label: post.data?.title || 'Post' })
  return items
})

const toggleLike = useCall({
  url: '/api/v2/method/my_new_app.api.toggle_like',
  method: 'POST',
  immediate: false,
  onSuccess: () => post.reload(),
})

const addComment = useCall({
  url: '/api/v2/method/my_new_app.api.add_comment',
  method: 'POST',
  immediate: false,
  onSuccess: () => {
    newComment.value = ''
    comments.reload()
    post.reload()
  },
})

const moreOptions = computed(() => {
  const opts = [{ label: 'Copy link', icon: 'lucide-link', onClick: () => copyLink() }]
  if (post.data?.author === session.user) {
    opts.unshift({
      label: 'Edit post',
      icon: 'lucide-pencil',
      onClick: () => router.push({ name: 'WritePost', params: { postId: route.params.postId } }),
    })
  }
  return opts
})

function like() {
  toggleLike.submit({ reference_type: 'Post', reference_name: route.params.postId })
}

const toggleCommentLikeCall = useCall({
  url: '/api/v2/method/my_new_app.api.toggle_like',
  method: 'POST',
  immediate: false,
})

function toggleCommentLike(comment) {
  toggleCommentLikeCall.submit({ reference_type: 'Post Comment', reference_name: comment.name }).then((result) => {
    const target = commentList.value.find((c) => c.name === comment.name)
    if (target) {
      target.liked_by_me = result.liked
      target.like_count = result.count
    }
  })
}

const toggleSave = useCall({
  url: '/api/v2/method/my_new_app.api.toggle_save_post',
  method: 'POST',
  immediate: false,
  onSuccess: (data) => {
    toast.success(data.saved ? 'Saved' : 'Removed from saved posts')
    post.reload()
  },
})

function handleSave() {
  toggleSave.submit({ post: route.params.postId })
}

const followUser = useCall({
  url: '/api/v2/method/my_new_app.follow.follow_user',
  method: 'POST',
  immediate: false,
  onSuccess: (data) => {
    post.reload()
    if (data.status === 'requested') toast.info('Follow request sent')
  },
})

const unfollowUser = useCall({
  url: '/api/v2/method/my_new_app.follow.unfollow_user',
  method: 'POST',
  immediate: false,
  onSuccess: () => post.reload(),
})

const authorFollowLabel = computed(() => {
  if (post.data?.author_following_by_me) return 'Following'
  if (post.data?.author_follow_pending) return 'Requested'
  return 'Follow'
})

function handleFollowClick() {
  if (post.data.author_following_by_me || post.data.author_follow_pending) {
    unfollowUser.submit({ user: post.data.author })
  } else {
    followUser.submit({ user: post.data.author })
  }
}

function submitComment() {
  if (!newComment.value.trim()) return
  addComment.submit({ post: route.params.postId, content: newComment.value })
}

function copyLink() {
  navigator.clipboard.writeText(window.location.href)
  toast.success('Link copied')
}

function readTime(content) {
  const div = document.createElement('div')
  div.innerHTML = content || ''
  const words = (div.textContent || '').trim().split(/\s+/).filter(Boolean).length
  return Math.max(1, Math.round(words / 200))
}

function formatDate(value) {
  if (!value) return ''
  return new Date(value).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

function timeAgo(value) {
  if (!value) return ''
  const seconds = Math.floor((Date.now() - new Date(value)) / 1000)
  const units = [
    ['year', 31536000],
    ['month', 2592000],
    ['day', 86400],
    ['hour', 3600],
    ['minute', 60],
  ]
  for (const [label, secs] of units) {
    const val = Math.floor(seconds / secs)
    if (val >= 1) return `${val} ${label}${val > 1 ? 's' : ''} ago`
  }
  return 'just now'
}
</script>
