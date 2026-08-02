<template>
  <PageHeader>
    <Breadcrumbs :items="[{ label: APP_NAME, route: '/' }, { label: 'Explore' }]" />
    <Button variant="ghost" icon-left="lucide-pencil" label="Write your story" route="/write" />
  </PageHeader>

  <ScrollArea class="h-[calc(100vh-3rem)]">
    <div class="mx-auto max-w-[760px] px-5 py-6">
      <div v-if="!myPostCount.loading && myPostCount.data === 0" class="mb-4 text-p-sm text-ink-gray-6">
        You haven't written anything yet.
        <router-link to="/write" class="text-ink-gray-9 underline">Write your first blog.</router-link>
      </div>

      <h1 class="text-3xl font-semibold text-ink-gray-9">Writings from people on {{ APP_NAME }}</h1>

      <TextInput
        v-model="searchQuery"
        class="mt-5"
        placeholder="Search"
        size="lg"
      >
        <template #prefix>
          <span class="lucide-search size-4 text-ink-gray-5" aria-hidden="true" />
        </template>
      </TextInput>

      <ScrollArea orientation="horizontal" class="mt-3 pb-1">
        <div class="flex items-center gap-2">
          <Badge
            v-for="cat in categoryList.data"
            :key="cat.name"
            :label="cat.title"
            :variant="activeCategory === cat.name ? 'solid' : 'outline'"
            theme="gray"
            size="lg"
            class="shrink-0 cursor-pointer select-none"
            @click="toggleCategory(cat.name)"
          >
            <template #suffix>
              <span
                class="lucide-x size-3 hover:text-ink-gray-9"
                aria-hidden="true"
                @click.stop="confirmDeleteCategory(cat)"
              />
            </template>
          </Badge>
          <button
            class="flex shrink-0 items-center gap-1 rounded-full border border-dashed border-outline-gray-3 px-3 py-1 text-sm text-ink-gray-6 hover:border-outline-gray-4 hover:text-ink-gray-8"
            @click="openCreateCategory"
          >
            <span class="lucide-plus size-3.5" aria-hidden="true" />
            New filter
          </button>
        </div>
      </ScrollArea>

      <LoadingText v-if="posts.loading && !posts.data" class="mt-10" :lines="4" />

      <div v-else-if="!posts.data || posts.data.length === 0" class="py-16 text-center">
        <p class="text-p-base text-ink-gray-6">No writings found.</p>
      </div>

      <div v-else class="mt-6 divide-y divide-outline-gray-1">
        <router-link
          v-for="post in posts.data"
          :key="post.name"
          :to="{ name: 'PostDetail', params: { postId: post.name } }"
          class="flex items-start justify-between gap-4 py-5"
        >
          <div class="min-w-0 flex-1">
            <div class="flex items-center gap-2">
              <Avatar :label="post.author_name || post.author" size="sm" />
              <span class="text-sm text-ink-gray-7">{{ post.author_name || post.author }}</span>
            </div>
            <div class="mt-2 text-lg-semibold text-ink-gray-9">
              {{ post.title || excerpt(post.content, 60) }}
            </div>
            <p class="mt-1 line-clamp-2 text-p-sm text-ink-gray-6">
              {{ excerpt(post.content, 160) }}
            </p>
            <div class="mt-2 text-xs text-ink-gray-5">
              {{ formatDate(post.creation) }} · {{ readTime(post.content) }} min read
            </div>
          </div>
          <img
            v-if="coverImageFor(post)"
            :src="coverImageFor(post)"
            class="h-20 w-24 shrink-0 rounded-md object-cover"
          />
        </router-link>
      </div>

      <div v-if="posts.data && posts.data.length" class="mt-6 flex items-center justify-center gap-4 text-sm">
        <button
          class="text-ink-gray-6 disabled:text-ink-gray-3"
          :disabled="!posts.hasPreviousPage"
          @click="goToPreviousPage"
        >
          Previous
        </button>
        <span class="text-ink-gray-9">Page {{ page }}</span>
        <button
          class="text-ink-gray-6 disabled:text-ink-gray-3"
          :disabled="!posts.hasNextPage"
          @click="goToNextPage"
        >
          Next
        </button>
      </div>
    </div>
  </ScrollArea>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import {
  Avatar,
  Badge,
  Breadcrumbs,
  Button,
  LoadingText,
  PageHeader,
  ScrollArea,
  TextInput,
  dialog,
  toast,
  useCall,
  useList,
} from 'frappe-ui'
import { session } from '@/data/session'
import { APP_NAME } from '@/utils/appName'

const categoryList = useCall({
  url: '/api/v2/method/my_new_app.api.list_categories',
})

const createCategory = useCall({
  url: '/api/v2/method/my_new_app.api.create_category',
  method: 'POST',
  immediate: false,
  onSuccess: (data) => {
    toast.success('Filter created')
    categoryList.reload()
    activeCategory.value = data.name
    page.value = 1
  },
  onError: (err) => toast.error(err.message),
})

function openCreateCategory() {
  dialog.prompt({
    title: 'Create a new filter',
    fields: [{ name: 'title', label: 'Name', required: true }],
    onConfirm: ({ values, close }) => {
      createCategory.submit({ title: values.title })
      close()
    },
  })
}

let pendingDeleteName = null
const deleteCategory = useCall({
  url: '/api/v2/method/my_new_app.api.delete_category',
  method: 'POST',
  immediate: false,
  onSuccess: () => {
    toast.success('Filter removed')
    if (activeCategory.value === pendingDeleteName) activeCategory.value = ''
    categoryList.reload()
  },
  onError: (err) => toast.error(err.message),
})

function confirmDeleteCategory(cat) {
  pendingDeleteName = cat.name
  dialog.confirm({
    title: 'Delete this filter?',
    message: `"${cat.title}" will be removed. It can't be deleted while posts still use it.`,
    confirmLabel: 'Delete',
    onConfirm: () => deleteCategory.submit({ name: cat.name }),
  })
}

const searchQuery = ref('')
const activeCategory = ref('')
const pageLength = 10
const page = ref(1)

function toggleCategory(cat) {
  activeCategory.value = activeCategory.value === cat ? '' : cat
  page.value = 1
}

const filters = computed(() => {
  const f = { status: 'Published' }
  if (activeCategory.value) f.category = activeCategory.value
  if (searchQuery.value) f.title = ['like', `%${searchQuery.value}%`]
  return f
})

const posts = useList({
  doctype: 'Post',
  fields: [
    'name',
    'title',
    'content',
    'post_type',
    'category',
    'attachment',
    'cover_image',
    'author',
    'author_name',
    'author_image',
    'creation',
  ],
  orderBy: 'creation desc',
  filters,
  limit: pageLength,
  refetch: true,
})

function goToNextPage() {
  posts.next()
  page.value += 1
}

function goToPreviousPage() {
  posts.previous()
  page.value = Math.max(1, page.value - 1)
}

watch(searchQuery, () => {
  page.value = 1
})

const myPostCount = useCall({
  url: '/api/v2/method/frappe.client.get_count',
  params: { doctype: 'Post', filters: JSON.stringify({ author: session.user }) },
})

function stripHtml(html) {
  const div = document.createElement('div')
  div.innerHTML = html || ''
  return div.textContent || div.innerText || ''
}

function excerpt(content, length) {
  const text = stripHtml(content).trim()
  return text.length > length ? text.slice(0, length) + '…' : text
}

function coverImageFor(post) {
  if (post.cover_image) return post.cover_image
  if (post.post_type !== 'Video') return post.attachment
  return null
}

function readTime(content) {
  const words = stripHtml(content).trim().split(/\s+/).filter(Boolean).length
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
</script>
