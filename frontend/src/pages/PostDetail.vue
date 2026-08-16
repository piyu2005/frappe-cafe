<template>
  <PageHeader v-if="!isMobile">
    <Breadcrumbs :items="breadcrumbItems" />
    <Button variant="solid" theme="gray" icon-left="lucide-plus" label="New Post" route="/write" />
  </PageHeader>
  <PageHeaderMobile v-else :title="post.data?.title || 'Post'">
    <template #left>
      <PageHeaderBackButton to="/" />
    </template>
  </PageHeaderMobile>

  <ScrollArea class="h-full">
    <div class="mx-auto max-w-[770px] px-4 py-6 sm:px-5 sm:py-8">
      <LoadingText v-if="post.loading && !post.data" :lines="8" />

      <div v-else-if="post.error && !post.data" class="flex flex-col items-center gap-3 py-24 text-center">
        <span class="lucide-lock size-8 text-ink-gray-3" aria-hidden="true" />
        <p class="text-p-base text-ink-gray-5">
          This post isn't available. It may be a draft, archived, or removed.
        </p>
      </div>

      <template v-else-if="post.data">
        <h1 class="text-3xl font-semibold text-ink-gray-9">{{ post.data.title }}</h1>

        <div class="mt-5 flex items-center gap-4">
          <Avatar
            :image="post.data.author_image"
            :label="post.data.author_name"
            size="3xl"
            class="size-20 author-avatar"
          />
          <div class="min-w-0 flex-1">
            <router-link
              :to="{ name: 'Profile', params: { userId: post.data.author } }"
              class="text-xl font-semibold text-ink-gray-9 hover:underline"
            >
              {{ post.data.author_name }}
            </router-link>
            <div class="mt-1 text-base text-ink-gray-5">
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
          <Dropdown :options="moreOptions">
            <Button icon="lucide-more-horizontal" />
          </Dropdown>
        </div>

        <hr class="mt-3 border-outline-gray-1" />

        <PostImageCarousel
          v-if="isImagePost"
          :images="post.data.images.map((i) => i.image)"
          class="mt-8"
        />

        <Editor
          ref="postEditorRef"
          :model-value="renderedContent"
          :extensions="readExtensions"
          :editable="false"
        >
          <template #default>
            <EditorContent class="mt-8" />
          </template>
        </Editor>

        <div v-if="post.data.tags.length" class="mt-6 flex flex-wrap gap-2">
          <Badge v-for="tag in post.data.tags" :key="tag" :label="tag" variant="subtle" size="lg" />
        </div>

        <div class="mt-8 flex items-center justify-between border-y border-outline-gray-1 py-3">
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
            <button
              type="button"
              class="flex items-center gap-1.5 text-sm text-ink-gray-6"
              @click="focusCommentBox"
            >
              <span class="lucide-message-circle size-4" aria-hidden="true" />
              {{ commentCount }}
            </button>
          </div>
          <div class="flex items-center gap-2">
            <Button icon="lucide-send" variant="outline" theme="gray" @click="openShareDialog" />
            <Button
              icon="lucide-bookmark"
              :variant="post.data.saved_by_me ? 'solid' : 'outline'"
              theme="gray"
              :loading="toggleSave.loading"
              @click="handleSave"
            />
          </div>
        </div>

        <h2 class="mt-6 text-lg-semibold text-ink-gray-9">Responses ({{ commentCount }})</h2>

        <div ref="commentBoxRef" class="mt-3">
          <FormControl
            v-model="newComment"
            type="textarea"
            placeholder="What are your thoughts?"
            :rows="3"
            @keydown.enter.exact="onCommentEnter"
          />
          <Button
            class="mt-2"
            variant="solid"
            theme="gray"
            label="Comment"
            @click="submitComment"
          />
        </div>

        <div class="mt-6 divide-y divide-outline-gray-1">
          <div v-for="c in visibleComments" :key="c._key" class="py-4">
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
              <button class="text-ink-gray-5 hover:underline" @click="toggleReplyBox(c)">Reply</button>
              <button
                v-if="c.comment_by === session.user"
                class="text-ink-gray-5 hover:underline"
                @click="confirmDeleteComment(c)"
              >
                Delete
              </button>
            </div>

            <div v-if="replyingTo === c.name" class="mt-2 pl-8">
              <FormControl
                v-model="replyText"
                type="textarea"
                :placeholder="`Reply to ${c.comment_by_name}`"
                :rows="2"
                @keydown.enter.exact="onReplyEnter($event, c)"
              />
              <div class="mt-1.5 flex gap-2">
                <Button variant="solid" theme="gray" label="Reply" size="sm" @click="submitReply(c)" />
                <Button variant="ghost" theme="gray" label="Cancel" size="sm" @click="cancelReply" />
              </div>
            </div>

            <button
              v-if="repliesFor(c.name).length && !expandedReplies.has(c.name)"
              class="mt-2 ml-8 flex items-center gap-1.5 text-xs text-ink-gray-5 hover:underline"
              @click="expandedReplies.add(c.name)"
            >
              <span class="h-px w-6 bg-outline-gray-2" aria-hidden="true" />
              View {{ repliesFor(c.name).length }} {{ repliesFor(c.name).length === 1 ? 'reply' : 'replies' }}
            </button>

            <div v-if="expandedReplies.has(c.name)" class="mt-2 ml-8 space-y-3">
              <div v-for="r in repliesFor(c.name)" :key="r._key">
                <div class="flex items-center gap-2">
                  <Avatar :image="r.comment_by_image" :label="r.comment_by_name" size="sm" />
                  <span class="text-sm-medium text-ink-gray-8">{{ r.comment_by_name }}</span>
                  <span class="text-xs text-ink-gray-5">{{ timeAgo(r.creation) }}</span>
                </div>
                <p class="mt-1 pl-8 text-p-sm text-ink-gray-7">{{ r.content }}</p>
                <div class="mt-1 flex items-center gap-3 pl-8 text-xs">
                  <button
                    class="flex items-center gap-1"
                    :class="r.liked_by_me ? 'text-ink-red-6' : 'text-ink-gray-5'"
                    @click="toggleCommentLike(r)"
                  >
                    <span
                      :class="r.liked_by_me ? 'lucide-heart fill-current' : 'lucide-heart'"
                      class="size-3"
                      aria-hidden="true"
                    />
                    {{ r.like_count }}
                  </button>
                  <button class="text-ink-gray-5 hover:underline" @click="toggleReplyBox(r)">Reply</button>
                  <button
                    v-if="r.comment_by === session.user"
                    class="text-ink-gray-5 hover:underline"
                    @click="confirmDeleteComment(r)"
                  >
                    Delete
                  </button>
                </div>

                <div v-if="replyingTo === r.name" class="mt-2 pl-8">
                  <FormControl
                    v-model="replyText"
                    type="textarea"
                    :placeholder="`Reply to ${r.comment_by_name}`"
                    :rows="2"
                    @keydown.enter.exact="onReplyEnter($event, r)"
                  />
                  <div class="mt-1.5 flex gap-2">
                    <Button variant="solid" theme="gray" label="Reply" size="sm" @click="submitReply(r)" />
                    <Button variant="ghost" theme="gray" label="Cancel" size="sm" @click="cancelReply" />
                  </div>
                </div>
              </div>

              <button
                class="ml-8 flex items-center gap-1.5 text-xs text-ink-gray-5 hover:underline"
                @click="expandedReplies.delete(c.name)"
              >
                Hide replies
              </button>
            </div>
          </div>
        </div>

        <button
          v-if="topLevelComments.length > visibleCount"
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
import { computed, nextTick, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Avatar,
  Badge,
  Breadcrumbs,
  Button,
  dialog,
  Dropdown,
  FormControl,
  LoadingText,
  PageHeader,
  PageHeaderBackButton,
  PageHeaderMobile,
  ScrollArea,
  toast,
  useCall,
} from 'frappe-ui'
import { Editor, EditorContent, ImageGroup, ImageViewer, RichTextKit } from 'frappe-ui/editor'
import { session } from '@/data/session'
import { ensureHtmlContent } from '@/utils/content'
import { APP_NAME } from '@/utils/appName'
import { applyImagePositions, PositionableImage } from '@/utils/positionableImage'
import { useIsMobile } from '@/composables/useIsMobile'

const isMobile = useIsMobile()
import PostImageCarousel from '@/components/PostImageCarousel.vue'

const router = useRouter()
// Underline is already part of frappe-ui's own StarterKit (on by default),
// which RichTextKit builds on — no need to add a second copy of the mark
// just to render posts that use it. `image: false` + explicit
// ImageGroup/ImageViewer matches WritePost.vue's editor setup (see its own
// comment for the full rationale) — PositionableImage is what lets a focal
// point chosen while writing actually render here.
// `color: false` matches WritePost.vue's editor — keeps this read-only render
// consistent with what was actually written, and means any content saved
// before that fix (with a stray pasted-in color) now falls back to the
// normal text color here too, instead of keeping the parsed Color mark.
const readExtensions = [
  RichTextKit.configure({ mention: false, tag: false, color: false, image: false }),
  PositionableImage,
  ImageGroup,
  ImageViewer,
]

const route = useRoute()
const newComment = ref('')
const commentBoxRef = ref(null)

async function focusCommentBox() {
  const el = commentBoxRef.value
  if (!el) return
  el.scrollIntoView({ behavior: 'smooth', block: 'center' })
  // Wait for the smooth scroll to land before focusing — focusing mid-scroll
  // makes the browser jump the box to the viewport edge instead.
  await nextTick()
  setTimeout(() => {
    el.querySelector('textarea')?.focus()
  }, 400)
}
const visibleCount = ref(5)

const post = useCall({
  url: '/api/v2/method/my_new_app.api.get_post',
  params: () => ({ post_id: route.params.postId }),
  refetch: true,
})

// Only needed to fill in an optimistic comment's avatar/name before the
// server round-trip confirms it (see submitComment/submitReply below).
const myProfile = useCall({
  url: '/api/v2/method/my_new_app.api.get_profile',
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
//
// vueuse's useFetch resets `data` to null the instant a reload starts (its
// `resetOnExecute` default), before the new response has actually arrived —
// so a reload would briefly null `comments.data`. Only syncing on a truthy
// value (rather than falling back to `[]`) keeps the previous list on screen
// through that gap instead of flashing it empty and back.
//
// Every row also carries a `_key` that's independent of `name` — used for
// `v-for` instead of `name` directly. An optimistically-added comment (see
// submitComment/submitReply) is later patched in place with the server's
// real fields once it's confirmed, `name` included, but keeps its original
// `_key` — so Vue's keyed diff sees the same element updating rather than
// one node disappearing and a different-keyed one taking its place, which is
// what was still causing a flicker even after the placeholder itself stopped
// waiting on a round-trip to appear.
const commentList = ref([])
watch(
  () => comments.data,
  (val) => {
    if (!val) return
    commentList.value = val.map((c) => ({ ...c, _key: c.name }))
  },
  { immediate: true },
)

const commentCount = computed(() => commentList.value.length)
const topLevelComments = computed(() => commentList.value.filter((c) => !c.parent_comment))
const visibleComments = computed(() => topLevelComments.value.slice(0, visibleCount.value))

function repliesFor(commentName) {
  return commentList.value
    .filter((c) => c.parent_comment === commentName)
    .slice()
    .reverse()
}

const expandedReplies = reactive(new Set())
const replyingTo = ref(null)
const replyText = ref('')

function toggleReplyBox(comment) {
  if (replyingTo.value === comment.name) {
    cancelReply()
    return
  }
  replyingTo.value = comment.name
  replyText.value = ''
}

function cancelReply() {
  replyingTo.value = null
  replyText.value = ''
}

// The list only ever reflected the new comment/reply after the round-trip to
// the server finished (`comments.reload()`), so it popped in and reflowed
// everything below it well after the keypress — perceived as a flicker.
// Inserting a local placeholder immediately makes it appear the instant
// Enter is pressed; `comments.reload()`'s eventual authoritative list just
// swaps the placeholder for the real row once it lands.
let tempCommentSeq = 0
function buildOptimisticComment(content, parentComment) {
  tempCommentSeq += 1
  const key = `temp-${Date.now()}-${tempCommentSeq}`
  return {
    _key: key,
    name: key,
    parent_comment: parentComment || null,
    comment_by: session.user,
    comment_by_name: myProfile.data?.full_name || session.user,
    comment_by_image: myProfile.data?.user_image || null,
    content,
    creation: new Date().toISOString(),
    like_count: 0,
    liked_by_me: false,
  }
}

function submitReply(comment) {
  const content = replyText.value.trim()
  if (!content) return
  const threadRoot = comment.parent_comment || comment.name
  replyingTo.value = null
  replyText.value = ''
  expandedReplies.add(threadRoot)

  const optimistic = buildOptimisticComment(content, threadRoot)
  commentList.value = [optimistic, ...commentList.value]

  addComment.submit({ post: route.params.postId, content, parent_comment: threadRoot }).then((result) => {
    const target = commentList.value.find((c) => c._key === optimistic._key)
    if (!target) return
    if (result) {
      // Patch in place rather than reloading the whole list — keeps the same
      // `_key`/DOM node, just fills in the real name/timestamp now that the
      // server has confirmed it.
      Object.assign(target, result, { like_count: 0, liked_by_me: false })
    } else {
      // Submission failed — drop the placeholder and give the reply back so
      // nothing typed is lost.
      commentList.value = commentList.value.filter((c) => c._key !== optimistic._key)
      replyingTo.value = comment.name
      replyText.value = content
    }
  })
}

// Enter submits, Shift+Enter still inserts a newline — `.exact` already keeps
// this handler from firing when Shift (or any other modifier) is held.
function onReplyEnter(e, comment) {
  e.preventDefault()
  submitReply(comment)
}

const deleteComment = useCall({
  url: '/api/v2/method/my_new_app.api.delete_comment',
  method: 'POST',
  immediate: false,
  onError: (err) => toast.error(err.message),
})

function confirmDeleteComment(comment) {
  dialog.danger({
    title: 'Delete comment?',
    message: 'This will permanently remove your comment.',
    onConfirm: () =>
      deleteComment.submit({ name: comment.name }).then(() => {
        // Mirror the backend's cascade: dropping a top-level comment takes
        // its replies with it too, rather than leaving them orphaned in the
        // local list until the next full reload.
        commentList.value = commentList.value.filter(
          (c) => c.name !== comment.name && c.parent_comment !== comment.name,
        )
        // Deleting the last reply in a thread would otherwise leave a
        // dangling "Hide replies" toggle with nothing under it.
        const threadRoot = comment.parent_comment || comment.name
        if (!commentList.value.some((c) => c.parent_comment === threadRoot)) {
          expandedReplies.delete(threadRoot)
        }
      }),
  })
}

const renderedContent = computed(() => ensureHtmlContent(post.data?.content))

// MediaNodeView (frappe-ui's image NodeView) never applies a custom
// objectPosition attribute to its own <img> — see positionableImage.js —
// so the focal point chosen while writing has to be pushed onto the DOM
// here too, once the read-only editor has actually rendered this content.
const postEditorRef = ref(null)
watch(renderedContent, async () => {
  await nextTick()
  applyImagePositions(postEditorRef.value?.editor)
})

const isImagePost = computed(
  () => post.data?.post_type === 'Image' && post.data?.images?.length > 0,
)

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
  // No comments.reload() here — the submit's own response already has the
  // confirmed comment (see submitComment/submitReply), which patches the
  // optimistic row in place. A reload would replace the whole list with
  // freshly-fetched objects for no benefit, right after that patch.
  onError: (err) => toast.error(err.message || 'Could not post comment'),
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
  const content = newComment.value.trim()
  if (!content) return
  newComment.value = ''

  const optimistic = buildOptimisticComment(content)
  commentList.value = [optimistic, ...commentList.value]

  addComment.submit({ post: route.params.postId, content }).then((result) => {
    const target = commentList.value.find((c) => c._key === optimistic._key)
    if (!target) return
    if (result) {
      Object.assign(target, result, { like_count: 0, liked_by_me: false })
    } else {
      commentList.value = commentList.value.filter((c) => c._key !== optimistic._key)
      newComment.value = content
    }
  })
}

function onCommentEnter(e) {
  e.preventDefault()
  submitComment()
}

function copyLink() {
  navigator.clipboard.writeText(window.location.href)
  toast.success('Link copied')
}

const shareablePeople = useCall({
  url: '/api/v2/method/my_new_app.api.list_people',
})

const startShareDm = useCall({
  url: '/api/v2/method/my_new_app.chat.start_dm',
  method: 'POST',
  immediate: false,
  onSuccess: (data) => {
    sendSharedPost.submit({ conversation: data.conversation, shared_post: route.params.postId })
  },
  onError: (err) => toast.error(err.message),
})

const sendSharedPost = useCall({
  url: '/api/v2/method/my_new_app.chat.send_message',
  method: 'POST',
  immediate: false,
  onSuccess: () => toast.success('Post shared'),
  onError: (err) => toast.error(err.message),
})

async function openShareDialog() {
  if (!shareablePeople.data) {
    await shareablePeople.reload()
  }
  dialog.prompt({
    title: 'Share this post',
    fields: [
      {
        name: 'user',
        label: 'Send to',
        type: 'combobox',
        required: true,
        options: (shareablePeople.data || []).map((p) => ({ label: p.full_name, value: p.name })),
      },
    ],
    onConfirm: ({ values, close }) => {
      startShareDm.submit({ other_user: values.user })
      close()
    },
  })
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

<style scoped>
/* Avatar's `size` prop only goes up to `3xl` (text-3xl), which reads small
   against the 80px circle this page uses — there's no bigger enum step, so
   reach past the label div's own class straight to a fixed size instead. */
.author-avatar :deep(.uppercase) {
  font-size: 2rem;
}

/*
 * Images inserted in the editor carry an explicit pixel width/height (the
 * source photo's natural size, unless the author manually resized it while
 * writing) baked into both the node wrapper's inline style and the <img>'s
 * width/height attributes. Left alone, a large source photo renders at its
 * raw pixel size instead of fitting the article column. Force both back to
 * fill the column width at a fixed height (matching the cover image treatment
 * above), cropping via object-fit so every content image reads as the same
 * consistent size regardless of the source photo's own aspect ratio.
 */
:deep(.not-prose) {
  width: 100% !important;
  height: 50vh !important;
  min-height: 240px !important;
}
/* The <img>/<video> sit inside their own unsized wrapper div — a percentage
   height can't resolve through an auto-height ancestor, so that wrapper
   needs to be stretched too before height:100% on the media itself works. */
:deep(.not-prose > div) {
  height: 100% !important;
}
:deep(.not-prose img),
:deep(.not-prose video) {
  width: 100% !important;
  height: 100% !important;
  object-fit: cover;
}
@media (min-width: 640px) {
  :deep(.not-prose) {
    height: 420px !important;
  }
}
</style>
