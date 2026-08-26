<template>
  <PageHeader v-if="!isMobile">
    <Breadcrumbs
      :items="[
        { label: APP_NAME, route: '/' },
        { label: 'Explore', route: '/' },
        { label: pub.data?.title || 'Publication' },
      ]"
    />
    <Button variant="solid" theme="gray" icon-left="lucide-plus" label="New Post" route="/write" />
  </PageHeader>
  <PageHeaderMobile v-else :title="pub.data?.title || 'Publication'">
    <template #right>
      <div class="flex items-center gap-1">
        <MobileNotificationBell />
        <Button variant="solid" theme="gray" icon="lucide-plus" route="/write" />
      </div>
    </template>
  </PageHeaderMobile>

  <ScrollArea class="h-[calc(100vh-52px)] md:h-[calc(100vh-3rem)]">
    <div class="mx-auto max-w-[760px] px-5 py-8">
      <LoadingText v-if="pub.loading && !pub.data" :lines="6" />

      <template v-else-if="pub.data">
        <div class="flex items-center gap-4">
          <div class="flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl bg-surface-gray-10">
            <span class="text-xl-semibold text-ink-base">{{ pub.data.title[0] }}</span>
          </div>

          <div class="min-w-0 flex-1">
            <div class="flex items-center gap-2">
              <h1 class="text-2xl font-semibold text-ink-gray-9">{{ pub.data.title }}</h1>
              <Button
                :variant="pub.data.subscribed_by_me ? 'outline' : 'solid'"
                theme="gray"
                :label="pub.data.subscribed_by_me ? 'Subscribed' : 'Subscribe'"
                :loading="subscribe.loading"
                @click="toggleSubscribe"
              />
              <Button icon="lucide-share-2" @click="copyLink" />
            </div>
            <div class="mt-1 flex items-center gap-1.5 text-sm text-ink-gray-5">
              <span v-if="pub.data.website" class="flex items-center gap-1">
                <span class="lucide-globe size-3.5" aria-hidden="true" />
                {{ pub.data.website }}
              </span>
              <span v-if="pub.data.website">·</span>
              <span>@{{ pub.data.handle }}</span>
            </div>
            <p v-if="pub.data.description" class="mt-2 text-p-sm text-ink-gray-7">
              {{ pub.data.description }}
            </p>

            <router-link
              :to="`/publications/${route.params.handle}/members`"
              class="mt-3 flex items-center gap-2 hover:opacity-80"
            >
              <div class="flex -space-x-2">
                <Avatar
                  v-for="m in pub.data.members"
                  :key="m.user"
                  :image="m.user_image"
                  :label="m.full_name"
                  size="sm"
                  class="ring-2 ring-surface-base"
                />
              </div>
              <span class="text-sm text-ink-gray-5">
                {{ pub.data.editor_count }} Editor{{ pub.data.editor_count === 1 ? '' : 's' }} ·
                {{ pub.data.member_count }} Member{{ pub.data.member_count === 1 ? '' : 's' }} ·
                {{ pub.data.subscriber_count }} Subscriber{{ pub.data.subscriber_count === 1 ? '' : 's' }}
              </span>
              <span class="lucide-arrow-right size-4 text-ink-gray-5" aria-hidden="true" />
            </router-link>
          </div>
        </div>

        <div class="mt-6 divide-y divide-outline-gray-1">
          <p v-if="pub.data.posts.length === 0" class="py-10 text-center text-p-base text-ink-gray-6">
            No posts yet.
          </p>
          <router-link
            v-for="post in pub.data.posts"
            :key="post.name"
            :to="{ name: 'PostDetail', params: { postId: post.name } }"
            class="flex items-start justify-between gap-4 py-5"
          >
            <div class="min-w-0 flex-1">
              <div class="text-base-medium text-ink-gray-9">{{ post.display_title || post.title || excerpt(post.content, 60) }}</div>
              <p class="mt-1 line-clamp-2 text-p-sm text-ink-gray-6">{{ excerpt(post.content, 160) }}</p>
              <div class="mt-2 text-xs text-ink-gray-5">
                {{ formatDate(post.creation) }} · {{ readTime(post.content) }} min read
              </div>
            </div>
            <img
              v-if="coverImageFor(post)"
              :src="coverImageFor(post)"
              loading="lazy"
              decoding="async"
              class="h-20 w-24 shrink-0 rounded-md object-cover"
            />
          </router-link>
        </div>
      </template>
    </div>
  </ScrollArea>
</template>

<script setup>
import { useRoute } from 'vue-router'
import {
  Avatar,
  Breadcrumbs,
  Button,
  LoadingText,
  PageHeader,
  PageHeaderMobile,
  ScrollArea,
  toast,
  useCall,
} from 'frappe-ui'
import { APP_NAME } from '@/utils/appName'
import MobileNotificationBell from '@/components/MobileNotificationBell.vue'
import { useIsMobile } from '@/composables/useIsMobile'

const isMobile = useIsMobile()
const route = useRoute()

const pub = useCall({
  url: '/api/v2/method/my_new_app.api.get_publication',
  params: () => ({ handle: route.params.handle }),
  refetch: true,
})

const subscribe = useCall({
  url: '/api/v2/method/my_new_app.api.toggle_subscribe',
  method: 'POST',
  immediate: false,
  onSuccess: () => pub.reload(),
})

function toggleSubscribe() {
  subscribe.submit({ reference_type: 'Publication', reference_name: route.params.handle })
}

function copyLink() {
  navigator.clipboard.writeText(window.location.href)
  toast.success('Link copied')
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

function coverImageFor(post) {
  if (post.cover_image) return post.cover_image
  if (post.post_type !== 'Video') return post.attachment
  return null
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
