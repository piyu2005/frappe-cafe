<template>
  <div>
    <LoadingText v-if="savedPosts.loading && !savedPosts.data" :lines="4" />
    <p v-else-if="savedPosts.data && savedPostsList.length === 0" class="text-p-base text-ink-gray-6">
      No saved posts yet.
    </p>
    <div v-else class="divide-y divide-outline-gray-1">
      <div v-for="p in savedPostsList" :key="p.name" class="flex items-center gap-3 py-6 first:pt-0">
        <router-link
          :to="{ name: 'PostDetail', params: { postId: p.name } }"
          class="flex min-w-0 flex-1 items-stretch gap-4"
          @click="emit('navigate')"
        >
          <div class="min-w-0 flex-1">
            <div class="truncate text-base-medium text-ink-gray-9">{{ p.display_title || p.title || 'Untitled' }}</div>
            <p class="mt-1 line-clamp-2 text-p-sm text-ink-gray-6">{{ excerpt(p.content, 140) }}</p>
            <div class="mt-1 text-xs text-ink-gray-5">By {{ p.author_name }}</div>
          </div>
          <img v-if="coverImageFor(p)" :src="coverImageFor(p)" class="h-20 w-24 shrink-0 rounded-md object-cover" />
        </router-link>
        <Button icon="lucide-bookmark-minus" variant="ghost" @click="unsave(p.name)" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { Button, LoadingText, useCall } from 'frappe-ui'

const emit = defineEmits(['navigate'])

const savedPosts = useCall({
  url: '/api/v2/method/my_new_app.api.list_saved_posts',
})

// Removing a post needs to drop it from the list the instant it's clicked,
// before the server confirms. savedPosts.data is useCall's read-only
// computed, so this keeps its own mutable copy.
const savedPostsList = ref([])
watch(
  () => savedPosts.data,
  (val) => {
    if (!val) return
    savedPostsList.value = val
  },
  { immediate: true },
)

const unsavePost = useCall({
  url: '/api/v2/method/my_new_app.api.toggle_save_post',
  method: 'POST',
  immediate: false,
})

function unsave(postId) {
  const previousList = savedPostsList.value
  savedPostsList.value = previousList.filter((p) => p.name !== postId)

  unsavePost.submit({ post: postId }).then((result) => {
    // A failed request, or a `saved` that came back true (a double-click
    // between the optimistic removal and this response), means the post is
    // still saved. Put it back.
    if (!result || result.saved) {
      savedPostsList.value = previousList
    }
  })
}

function coverImageFor(post) {
  if (post.cover_image) return post.cover_image
  if (post.post_type !== 'Video') return post.attachment
  return null
}

function excerpt(content, length) {
  const div = document.createElement('div')
  div.innerHTML = content || ''
  const text = (div.textContent || '').trim()
  return text.length > length ? text.slice(0, length) + '…' : text
}
</script>
