<template>
  <PageHeader>
    <Breadcrumbs :items="[{ label: APP_NAME, route: '/' }, { label: 'Messages' }]" />
  </PageHeader>

  <div class="flex h-[calc(100vh-3rem)]">
    <!-- Conversation list -->
    <div class="flex w-80 shrink-0 flex-col border-r border-outline-gray-1">
      <div class="border-b border-outline-gray-1 p-3">
        <TextInput v-model="search" placeholder="Search by name">
          <template #prefix>
            <span class="lucide-search size-4 text-ink-gray-5" aria-hidden="true" />
          </template>
        </TextInput>
      </div>

      <ScrollArea class="flex-1">
        <template v-if="!showingPeopleSearch">
          <LoadingText v-if="conversations.loading && !conversations.data" class="p-3" :lines="4" />
          <p v-else-if="!conversations.data || !conversations.data.length" class="p-4 text-center text-p-sm text-ink-gray-5">
            No conversations yet.
          </p>
          <button
            v-for="c in conversations.data"
            :key="c.conversation"
            class="flex w-full items-center gap-3 px-3 py-3 text-left hover:bg-surface-gray-1"
            :class="{ 'bg-surface-gray-2': c.conversation === activeConversationId }"
            @click="openConversation(c.conversation)"
          >
            <Avatar :image="c.display_image" :label="c.display_name" size="md" />
            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-1.5">
                <span class="truncate text-base-medium text-ink-gray-9">{{ c.display_name }}</span>
                <span v-if="c.muted" class="lucide-bell-off size-3 shrink-0 text-ink-gray-4" aria-hidden="true" />
              </div>
              <p class="truncate text-sm text-ink-gray-5">{{ c.last_message || 'No messages yet' }}</p>
            </div>
            <span
              v-if="c.unread_count > 0"
              class="grid h-5 min-w-5 shrink-0 place-content-center rounded-full bg-surface-gray-10 px-1 text-2xs text-ink-base"
            >
              {{ c.unread_count }}
            </span>
          </button>
        </template>

        <template v-else>
          <LoadingText v-if="peopleSearch.loading && !peopleSearch.data" class="p-3" :lines="4" />
          <p v-else-if="peopleSearch.data && peopleSearch.data.length === 0" class="p-4 text-center text-p-sm text-ink-gray-5">
            No people found.
          </p>
          <button
            v-for="p in peopleSearch.data"
            :key="p.name"
            class="flex w-full items-center gap-3 px-3 py-3 text-left hover:bg-surface-gray-1"
            :disabled="startDm.loading"
            @click="startDm.submit({ other_user: p.name })"
          >
            <Avatar :image="p.user_image" :label="p.full_name" size="md" />
            <div class="min-w-0 flex-1">
              <span class="truncate text-base-medium text-ink-gray-9">{{ p.full_name }}</span>
            </div>
          </button>
        </template>
      </ScrollArea>
    </div>

    <!-- Thread -->
    <div class="flex min-w-0 flex-1 flex-col">
      <div v-if="!activeConversationId" class="flex flex-1 items-center justify-center">
        <p class="text-p-base text-ink-gray-5">Select a conversation to start messaging.</p>
      </div>

      <template v-else-if="conversation.data">
        <div class="flex items-center justify-between border-b border-outline-gray-1 px-4 py-3">
          <div class="flex items-center gap-3">
            <Avatar :image="conversation.data.display_image" :label="conversation.data.display_name" size="md" />
            <div>
              <router-link
                v-if="conversation.data.other_user"
                :to="{ name: 'Profile', params: { userId: conversation.data.other_user } }"
                class="text-base-medium text-ink-gray-9 hover:underline"
              >
                {{ conversation.data.display_name }}
              </router-link>
              <div v-else class="text-base-medium text-ink-gray-9">{{ conversation.data.display_name }}</div>
              <div v-if="typingUser" class="text-xs text-ink-gray-5">typing…</div>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <button class="text-ink-gray-5 hover:text-ink-gray-9" @click="searchOpen = !searchOpen">
              <span class="lucide-search size-4" aria-hidden="true" />
            </button>
            <Dropdown :options="threadOptions">
              <Button icon="lucide-more-horizontal" />
            </Dropdown>
          </div>
        </div>

        <div v-if="searchOpen" class="border-b border-outline-gray-1 p-3">
          <TextInput v-model="messageSearchQuery" placeholder="Search in this conversation" @input="onSearchInput" />
          <div v-if="searchResults.data && searchResults.data.length" class="mt-2 space-y-1">
            <div v-for="r in searchResults.data" :key="r.name" class="rounded px-2 py-1 text-sm text-ink-gray-7 hover:bg-surface-gray-1">
              <span class="font-medium text-ink-gray-9">{{ r.sender_name }}:</span> {{ r.content }}
            </div>
          </div>
          <p v-else-if="messageSearchQuery" class="mt-2 text-sm text-ink-gray-5">No matches.</p>
        </div>

        <div v-if="conversation.data.is_blocked" class="border-b border-outline-gray-1 bg-surface-amber-2 px-4 py-2 text-sm text-ink-gray-7">
          <template v-if="conversation.data.i_blocked_them">
            You've blocked this user. Unblock them to send messages.
          </template>
          <template v-else>You can't reply to this conversation.</template>
        </div>

        <ScrollArea ref="scrollAreaRef" class="flex-1 px-4 py-3">
          <LoadingText v-if="messages.loading && !messageList.length" :lines="6" />
          <div v-else class="space-y-4">
            <div
              v-for="m in messageList"
              :key="m.name"
              class="group flex items-end gap-2"
              :class="m.sender === session.user ? 'flex-row-reverse' : ''"
            >
              <Avatar v-if="m.sender !== session.user" :image="m.sender_image" :label="m.sender_name" size="sm" />
              <div class="max-w-[70%]">
                <div
                  class="relative rounded-lg bg-surface-gray-2 px-3 py-2 text-sm text-ink-gray-9"
                >
                  <!-- Messages written with the rich-text composer store HTML;
                       older messages sent before it existed are plain text
                       with light markdown, still parsed the original way. -->
                  <Editor
                    v-if="isHtmlContent(m.content)"
                    :model-value="m.content"
                    :extensions="composerExtensions"
                    :editable="false"
                  >
                    <template #default>
                      <EditorContent class="prose-sm" />
                    </template>
                  </Editor>
                  <div v-else-if="m.content" class="whitespace-pre-wrap">
                    <template v-for="(t, i) in parseRichText(m.content)" :key="i">
                      <strong v-if="t.type === 'bold'">{{ t.value }}</strong>
                      <em v-else-if="t.type === 'italic'">{{ t.value }}</em>
                      <code v-else-if="t.type === 'code'" class="rounded bg-black/10 px-1 text-xs">{{ t.value }}</code>
                      <a
                        v-else-if="t.type === 'link'"
                        :href="t.value"
                        target="_blank"
                        rel="noopener"
                        class="underline"
                      >{{ t.value }}</a>
                      <template v-else>{{ t.value }}</template>
                    </template>
                  </div>
                  <div v-if="m.attachments && m.attachments.length" class="mt-1 flex flex-wrap gap-1.5">
                    <template v-for="(a, i) in m.attachments" :key="i">
                      <img
                        v-if="isImageFile(a.file_name)"
                        :src="a.file_url"
                        class="max-h-64 rounded object-cover"
                      />
                      <a
                        v-else
                        :href="a.file_url"
                        target="_blank"
                        rel="noopener"
                        class="flex items-center gap-2 rounded-lg border border-outline-gray-2 bg-surface-base px-2 py-1.5 text-xs text-ink-gray-8 no-underline hover:bg-surface-gray-1"
                      >
                        <span class="lucide-file size-3.5 shrink-0 text-ink-gray-5" aria-hidden="true" />
                        <span class="max-w-32 truncate">{{ a.file_name }}</span>
                      </a>
                    </template>
                  </div>

                  <button
                    v-if="m.shared_post"
                    class="mt-2 flex w-64 items-center gap-3 overflow-hidden rounded-lg border border-outline-gray-1 bg-surface-base p-2 text-left"
                    @click="router.push(m.link_url)"
                  >
                    <img
                      v-if="m.link_image"
                      :src="m.link_image"
                      class="size-14 shrink-0 rounded object-cover"
                    />
                    <div
                      v-else
                      class="grid size-14 shrink-0 place-content-center rounded bg-surface-gray-3"
                    >
                      <span class="lucide-image size-5 text-ink-gray-4" aria-hidden="true" />
                    </div>
                    <div class="min-w-0">
                      <div class="truncate text-sm font-medium text-ink-gray-9">{{ m.link_title }}</div>
                      <p v-if="m.link_description" class="truncate text-xs text-ink-gray-5">
                        {{ m.link_description }}
                      </p>
                      <span class="text-xs text-ink-gray-5">View post</span>
                    </div>
                  </button>

                  <a
                    v-else-if="m.link_url"
                    :href="m.link_url"
                    target="_blank"
                    rel="noopener"
                    class="mt-2 block overflow-hidden rounded border border-outline-gray-1"
                  >
                    <img v-if="m.link_image" :src="m.link_image" class="h-28 w-full object-cover" />
                    <div class="p-2">
                      <div class="truncate text-xs font-medium">{{ m.link_title }}</div>
                      <p v-if="m.link_description" class="mt-0.5 line-clamp-2 text-xs opacity-80">
                        {{ m.link_description }}
                      </p>
                    </div>
                  </a>

                  <Popover>
                    <template #trigger>
                      <button
                        class="absolute -top-3 hidden size-6 items-center justify-center rounded-full border border-outline-gray-1 bg-surface-base text-ink-gray-6 group-hover:flex"
                        :class="m.sender === session.user ? '-left-3' : '-right-3'"
                      >
                        <span class="lucide-smile-plus size-3.5" aria-hidden="true" />
                      </button>
                    </template>
                    <template #default="{ close }">
                      <div class="flex gap-1 p-1.5">
                        <button
                          v-for="e in emojiOptions"
                          :key="e"
                          class="rounded p-1 text-lg hover:bg-surface-gray-2"
                          @click="toggleReaction(m.name, e), close()"
                        >
                          {{ e }}
                        </button>
                      </div>
                    </template>
                  </Popover>
                </div>

                <div v-if="m.reactions && m.reactions.length" class="mt-1 flex flex-wrap gap-1" :class="m.sender === session.user ? 'justify-end' : ''">
                  <button
                    v-for="r in m.reactions"
                    :key="r.emoji"
                    class="flex items-center gap-1 rounded-full border px-1.5 py-0.5 text-xs"
                    :class="r.reacted_by_me ? 'border-outline-gray-3 bg-surface-gray-2' : 'border-outline-gray-1'"
                    @click="toggleReaction(m.name, r.emoji)"
                  >
                    {{ r.emoji }} {{ r.count }}
                  </button>
                </div>

                <div class="mt-0.5 text-xs text-ink-gray-4" :class="m.sender === session.user ? 'text-right' : ''">
                  {{ formatTime(m.creation) }}
                </div>
                <div
                  v-if="m.name === lastOwnMessage?.name && isSeenByOther"
                  class="text-right text-xs text-ink-gray-4"
                >
                  Seen
                </div>
              </div>
            </div>
          </div>
        </ScrollArea>

        <div class="border-t border-outline-gray-1 p-3">
          <Editor
            ref="composerEditorRef"
            v-model="newMessageText"
            :extensions="composerExtensions"
            placeholder="Write a message…"
            :editable="!conversation.data.is_blocked"
          >
            <template #default>
              <div class="rounded-lg border border-outline-gray-2 bg-surface-base focus-within:border-outline-gray-4">
                <div v-if="pendingAttachments.length" class="flex flex-wrap gap-2 p-2 pb-0">
                  <div
                    v-for="(a, i) in pendingAttachments"
                    :key="i"
                    class="flex w-56 items-center gap-2 rounded-lg border border-outline-gray-2 p-2"
                  >
                    <img
                      v-if="isImageFile(a.file_name)"
                      :src="a.file_url"
                      class="size-8 shrink-0 rounded-full object-cover"
                    />
                    <div v-else class="grid size-8 shrink-0 place-content-center rounded-full bg-surface-gray-3">
                      <span class="lucide-file size-3.5 text-ink-gray-5" aria-hidden="true" />
                    </div>
                    <div class="min-w-0 flex-1">
                      <div class="truncate text-sm-medium text-ink-gray-9">{{ a.file_name }}</div>
                      <div class="text-xs text-ink-gray-5">{{ formatBytes(a.file_size) }}</div>
                    </div>
                    <button
                      type="button"
                      class="flex size-6 shrink-0 items-center justify-center rounded text-ink-gray-5 hover:bg-surface-gray-2 hover:text-ink-gray-8"
                      @click="clearPendingAttachment(i)"
                    >
                      <span class="lucide-trash-2 size-3.5" aria-hidden="true" />
                    </button>
                  </div>
                </div>

                <div v-if="showFormatting" class="border-b border-outline-gray-1 px-2 py-1.5">
                  <EditorFixedMenu :items="composerToolbar" class="flex-wrap" />
                </div>

                <EditorContent
                  class="prose-sm max-h-32 overflow-y-auto px-3 pb-1 pt-2.5 text-ink-gray-9"
                  @keydown.enter.exact="onComposerEnter"
                />

                <div class="flex items-center justify-between px-1.5 pb-1.5">
                  <TooltipProvider :hover-delay="0.4" :skip-delay="0.3">
                    <div class="flex items-center gap-0.5">
                      <FileUploader ref="fileUploaderRef" @success="onFileUploaded">
                        <template #default="{ uploading, openFileSelector }">
                          <Tooltip text="Attach file">
                            <button
                              type="button"
                              class="flex size-7 items-center justify-center rounded text-ink-gray-5 hover:bg-surface-gray-2 hover:text-ink-gray-8 disabled:opacity-50"
                              :disabled="uploading || conversation.data.is_blocked"
                              @click="openFileSelector"
                            >
                              <span class="lucide-paperclip size-4" aria-hidden="true" />
                            </button>
                          </Tooltip>
                        </template>
                      </FileUploader>

                      <Tooltip text="Formatting">
                        <button
                          type="button"
                          class="flex size-7 items-center justify-center rounded text-ink-gray-5 hover:bg-surface-gray-2 hover:text-ink-gray-8 disabled:opacity-50"
                          :class="showFormatting ? 'bg-surface-gray-3 text-ink-gray-8' : ''"
                          :disabled="conversation.data.is_blocked"
                          @click="showFormatting = !showFormatting"
                        >
                          <span class="lucide-type size-4" aria-hidden="true" />
                        </button>
                      </Tooltip>

                      <Tooltip text="Mention">
                        <button
                          type="button"
                          class="flex size-7 items-center justify-center rounded text-ink-gray-5 hover:bg-surface-gray-2 hover:text-ink-gray-8 disabled:opacity-50"
                          :disabled="conversation.data.is_blocked"
                          @click="toast.info('Mentions are coming soon')"
                        >
                          <span class="lucide-at-sign size-4" aria-hidden="true" />
                        </button>
                      </Tooltip>

                      <Tooltip text="Emoji">
                        <Popover>
                          <template #trigger>
                            <button
                              type="button"
                              class="flex size-7 items-center justify-center rounded text-ink-gray-5 hover:bg-surface-gray-2 hover:text-ink-gray-8 disabled:opacity-50"
                              :disabled="conversation.data.is_blocked"
                            >
                              <span class="lucide-smile-plus size-4" aria-hidden="true" />
                            </button>
                          </template>
                          <template #default="{ close }">
                            <div class="grid w-64 max-h-56 grid-cols-8 gap-0.5 overflow-y-auto p-1.5">
                              <button
                                v-for="e in composerEmojiOptions"
                                :key="e"
                                type="button"
                                class="rounded p-1 text-lg hover:bg-surface-gray-2"
                                @click="selectEmoji(e), close()"
                              >
                                {{ e }}
                              </button>
                            </div>
                          </template>
                        </Popover>
                      </Tooltip>

                      <span class="mx-1 h-4 w-px bg-outline-gray-2" aria-hidden="true" />

                      <Tooltip text="Poll">
                        <button
                          type="button"
                          class="flex size-7 items-center justify-center rounded text-ink-gray-5 hover:bg-surface-gray-2 hover:text-ink-gray-8 disabled:opacity-50"
                          :disabled="conversation.data.is_blocked"
                          @click="toast.info('Polls are coming soon')"
                        >
                          <span class="lucide-bar-chart-2 size-4" aria-hidden="true" />
                        </button>
                      </Tooltip>

                      <Tooltip text="Attach a document from the system">
                        <button
                          type="button"
                          class="flex size-7 items-center justify-center rounded text-ink-gray-5 hover:bg-surface-gray-2 hover:text-ink-gray-8 disabled:opacity-50"
                          :disabled="conversation.data.is_blocked"
                          @click="toast.info('Attaching existing documents is coming soon')"
                        >
                          <span class="lucide-image-plus size-4" aria-hidden="true" />
                        </button>
                      </Tooltip>
                    </div>
                  </TooltipProvider>
                  <Button
                    variant="solid"
                    theme="gray"
                    icon="lucide-send"
                    :loading="sendMessage.loading"
                    :disabled="conversation.data.is_blocked"
                    @click="submitMessage"
                  />
                </div>
              </div>
            </template>
          </Editor>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Avatar,
  Breadcrumbs,
  Button,
  Dropdown,
  FileUploader,
  LoadingText,
  PageHeader,
  Popover,
  ScrollArea,
  TextInput,
  Tooltip,
  TooltipProvider,
  dialog,
  formatBytes,
  toast,
  useCall,
} from 'frappe-ui'
import {
  Blockquote,
  Bold,
  BulletList,
  CommentKit,
  Editor,
  EditorContent,
  EditorFixedMenu,
  FontHighlight,
  Highlight,
  InlineCode,
  InsertLink,
  Italic,
  OrderedList,
  Strike,
} from 'frappe-ui/editor'
import { session } from '@/data/session'
import { getSocket } from '@/data/socket'
import { parseRichText } from '@/utils/richText'
import { unreadMessageCount } from '@/data/messages'
import { APP_NAME } from '@/utils/appName'

const route = useRoute()
const router = useRouter()

const search = ref('')
const newMessageText = ref('')
const pendingAttachments = ref([])
const typingUser = ref(null)
const searchOpen = ref(false)
const messageSearchQuery = ref('')
const scrollAreaRef = ref(null)
const composerEditorRef = ref(null)
const fileUploaderRef = ref(null)
const showFormatting = ref(false)
const emojiOptions = ['👍', '❤️', '😂', '😮', '😢', '🎉']
const composerEmojiOptions = [
  '😀', '😃', '😄', '😁', '😆', '😅', '🤣', '😂', '🙂', '😉',
  '😊', '😇', '🥰', '😍', '😘', '😋', '😜', '🤪', '🤗', '🤔',
  '😐', '😑', '😶', '🙄', '😴', '😪', '😷', '🤒', '🥳', '😎',
  '🥺', '😭', '😢', '😡', '😠', '🤯', '😱', '😨', '😰', '🥶',
  '👍', '👎', '👏', '🙌', '🙏', '💪', '👋', '🤝', '✌️', '🤞',
  '❤️', '🧡', '💛', '💚', '💙', '💜', '🖤', '🤍', '💕', '💯',
  '🎉', '🎊', '🔥', '✨', '⭐', '🌟', '💡', '👀', '🚀', '🎯',
]

// Enter sends the message (chat convention); Shift-Enter still inserts a
// line break via the editor's own default handling of that combination. A
// plain native keydown listener avoids depending on `@tiptap/core` directly
// in app code — see the comment on `composerExtensions` below for why that
// matters here.
function onComposerEnter(e) {
  if (e.shiftKey) return
  e.preventDefault()
  submitMessage()
}

// frappe-ui doesn't ship ready-made toolbar buttons for underline, clearing
// formatting, or code blocks, so these follow the same public `CommandMenuItem`
// shape used by the exported items above — the documented escape hatch for
// exactly this case (see WritePost.vue's UnderlineItem for the same pattern).
const UnderlineItem = {
  label: 'Underline',
  icon: 'lucide-underline',
  action: (editor) => editor.chain().focus().toggleUnderline().run(),
  isActive: (editor) => editor.isActive('underline'),
}

const ClearFormatItem = {
  label: 'Clear formatting',
  icon: 'lucide-remove-formatting',
  action: (editor) => editor.chain().focus().unsetAllMarks().run(),
}

const CodeBlockItem = {
  label: 'Code block',
  icon: 'lucide-braces',
  action: (editor) => editor.chain().focus().toggleCodeBlock().run(),
  isActive: (editor) => editor.isActive('codeBlock'),
}

const composerToolbar = [
  Bold,
  Italic,
  UnderlineItem,
  Strike,
  FontHighlight,
  ClearFormatItem,
  InlineCode,
  CodeBlockItem,
  BulletList,
  OrderedList,
  Blockquote,
  InsertLink,
]

// CommentKit ("comments, chat, replies" per frappe-ui) is the lighter stack
// vs RichTextKit — no headings/tables/task-lists. Media/mention/tag/emoji are
// disabled since this app attaches files and picks emoji through its own UI
// below, not the editor's built-in nodes. Underline is already part of
// frappe-ui's own StarterKit (on by default), so it just needs the toolbar
// button above. Highlight isn't part of CommentKit's defaults, so it's added
// here directly — both are pulled in only through `frappe-ui/editor`'s own
// exports, never a direct `@tiptap/*` import (see vite.config.js's
// optimizeDeps comment for why that matters).
const composerExtensions = [
  CommentKit.configure({
    mention: false,
    tag: false,
    image: false,
    imageGroup: false,
    imageViewer: false,
    video: false,
    attachment: false,
    emoji: false,
  }),
  Highlight,
]

function isHtmlContent(text) {
  return /<[a-z][\s\S]*>/i.test(text || '')
}

let typingClearTimer = null
let typingThrottled = false

const activeConversationId = computed(() => route.params.conversationId || null)

const conversations = useCall({
  url: '/api/v2/method/my_new_app.chat.list_conversations',
  refetch: true,
})

const conversation = useCall({
  url: '/api/v2/method/my_new_app.chat.get_conversation',
  params: () => ({ conversation: activeConversationId.value }),
  immediate: false,
})

const messages = useCall({
  url: '/api/v2/method/my_new_app.chat.get_messages',
  params: () => ({ conversation: activeConversationId.value }),
  immediate: false,
})

// useCall's `.data` is a read-only computed (no setter) — keep our own
// mutable copy so realtime events / optimistic updates can push into it.
const messageList = ref([])
watch(
  () => messages.data,
  (val) => {
    messageList.value = val ? [...val] : []
  },
)

const showingPeopleSearch = computed(() => search.value.trim().length > 0)

const peopleSearch = useCall({
  url: '/api/v2/method/my_new_app.chat.search_people_to_message',
  params: () => ({ query: search.value }),
  immediate: false,
})

let searchDebounce = null
watch(search, (val) => {
  clearTimeout(searchDebounce)
  if (!val.trim()) return
  searchDebounce = setTimeout(() => peopleSearch.reload(), 200)
})

const searchResults = useCall({
  url: '/api/v2/method/my_new_app.chat.search_messages',
  params: () => ({ conversation: activeConversationId.value, query: messageSearchQuery.value }),
  immediate: false,
})

const markRead = useCall({
  url: '/api/v2/method/my_new_app.chat.mark_read',
  method: 'POST',
  immediate: false,
  onSuccess: () => {
    conversations.reload()
    unreadMessageCount.reload()
  },
})

const lastOwnMessage = computed(() => {
  const own = messageList.value.filter((m) => m.sender === session.user)
  return own.length ? own[own.length - 1] : null
})

const isSeenByOther = computed(() => {
  if (!lastOwnMessage.value || !conversation.data?.other_last_read) return false
  return new Date(conversation.data.other_last_read) >= new Date(lastOwnMessage.value.creation)
})

function scrollToBottom() {
  nextTick(() => {
    const el = scrollAreaRef.value?.$el?.querySelector('[data-reka-scroll-area-viewport]') || scrollAreaRef.value?.$el
    if (el) el.scrollTop = el.scrollHeight
  })
}

async function openConversationData(id) {
  typingUser.value = null
  searchOpen.value = false
  messageSearchQuery.value = ''
  if (!id) return
  await Promise.all([conversation.reload(), messages.reload()])
  markRead.submit({ conversation: id })
  scrollToBottom()
}

watch(activeConversationId, openConversationData, { immediate: true })

function openConversation(id) {
  router.push({ name: 'Messages', params: { conversationId: id } })
}

const startDm = useCall({
  url: '/api/v2/method/my_new_app.chat.start_dm',
  method: 'POST',
  immediate: false,
  onSuccess: (data) => {
    search.value = ''
    conversations.reload()
    openConversation(data.conversation)
  },
  onError: (err) => toast.error(err.message),
})

const sendMessage = useCall({
  url: '/api/v2/method/my_new_app.chat.send_message',
  method: 'POST',
  immediate: false,
  onSuccess: (msg) => {
    messageList.value = [...messageList.value, msg]
    newMessageText.value = ''
    pendingAttachments.value = []
    conversations.reload()
    scrollToBottom()
  },
  onError: (err) => toast.error(err.message),
})

function submitMessage() {
  const editor = composerEditorRef.value?.editor
  const isEmpty = !editor || editor.isEmpty
  if ((isEmpty && !pendingAttachments.value.length) || !activeConversationId.value) return
  sendMessage.submit({
    conversation: activeConversationId.value,
    content: isEmpty ? null : newMessageText.value,
    attachments: pendingAttachments.value.map((a) => ({
      file_url: a.file_url,
      file_name: a.file_name,
      file_size: a.file_size,
    })),
  })
}

function isImageFile(fileName) {
  return /\.(jpe?g|png|gif|webp)$/i.test(fileName || '')
}

// Resetting the underlying <input type="file">'s value after every pick is
// required so selecting the same file again later still fires a change
// event — browsers don't re-fire it when the file list is unchanged.
function onFileUploaded(file) {
  pendingAttachments.value = [
    ...pendingAttachments.value,
    { file_url: file.file_url, file_name: file.file_name, file_size: file.file_size },
  ]
  const inputEl = fileUploaderRef.value?.inputRef?.()
  if (inputEl) inputEl.value = ''
}

function clearPendingAttachment(index) {
  pendingAttachments.value = pendingAttachments.value.filter((_, i) => i !== index)
}

const setTypingCall = useCall({
  url: '/api/v2/method/my_new_app.chat.set_typing',
  method: 'POST',
  immediate: false,
})

function selectEmoji(e) {
  composerEditorRef.value?.editor?.chain().focus().insertContent(e).run()
}

watch(newMessageText, () => {
  if (!activeConversationId.value || typingThrottled) return
  typingThrottled = true
  setTypingCall.submit({ conversation: activeConversationId.value })
  setTimeout(() => (typingThrottled = false), 2000)
})

function onSearchInput() {
  if (messageSearchQuery.value.trim()) searchResults.reload()
}

const toggleReactionCall = useCall({
  url: '/api/v2/method/my_new_app.chat.toggle_reaction',
  method: 'POST',
  immediate: false,
  onSuccess(reactions) {
    const messageId = toggleReactionCall.params?.message
    const msg = messageList.value.find((m) => m.name === messageId)
    if (msg) msg.reactions = reactions
  },
})

function toggleReaction(message, emoji) {
  toggleReactionCall.submit({ message, emoji })
}

const muteCall = useCall({
  url: '/api/v2/method/my_new_app.chat.mute_conversation',
  method: 'POST',
  immediate: false,
  onSuccess: () => {
    conversation.reload()
    conversations.reload()
  },
})

const blockCall = useCall({
  url: '/api/v2/method/my_new_app.chat.block_user',
  method: 'POST',
  immediate: false,
  onSuccess: () => {
    conversation.reload()
    toast.success('User blocked')
  },
})

const unblockCall = useCall({
  url: '/api/v2/method/my_new_app.chat.unblock_user',
  method: 'POST',
  immediate: false,
  onSuccess: () => {
    conversation.reload()
    toast.success('User unblocked')
  },
})

const threadOptions = computed(() => {
  if (!conversation.data) return []
  const opts = [
    {
      label: conversation.data.muted ? 'Unmute' : 'Mute',
      icon: conversation.data.muted ? 'lucide-bell' : 'lucide-bell-off',
      onClick: () =>
        muteCall.submit({ conversation: activeConversationId.value, muted: conversation.data.muted ? 0 : 1 }),
    },
  ]
  if (conversation.data.other_user) {
    if (conversation.data.i_blocked_them) {
      opts.push({
        label: 'Unblock',
        icon: 'lucide-shield-check',
        onClick: () => unblockCall.submit({ user: conversation.data.other_user }),
      })
    } else {
      opts.push({
        label: 'Block',
        icon: 'lucide-shield-ban',
        onClick: () =>
          dialog.confirm({
            title: 'Block this user?',
            message: 'They will no longer be able to message you.',
            theme: 'red',
            confirmLabel: 'Block',
            onConfirm: () => blockCall.submit({ user: conversation.data.other_user }),
          }),
      })
    }
  }
  return opts
})

function handleNewMessage(payload) {
  conversations.reload()
  if (payload.conversation === activeConversationId.value) {
    messageList.value = [...messageList.value, payload]
    scrollToBottom()
    markRead.submit({ conversation: activeConversationId.value })
  }
}

function handleTyping(payload) {
  if (payload.conversation !== activeConversationId.value) return
  typingUser.value = payload.user
  clearTimeout(typingClearTimer)
  typingClearTimer = setTimeout(() => (typingUser.value = null), 3000)
}

function handleRead(payload) {
  if (payload.conversation === activeConversationId.value && conversation.data) {
    conversation.data.other_last_read = new Date().toISOString()
  }
}

function handleReaction(payload) {
  const msg = messageList.value.find((m) => m.name === payload.message)
  if (msg) msg.reactions = payload.reactions
}

let socket = null
onMounted(() => {
  socket = getSocket()
  socket.on('chat:new_message', handleNewMessage)
  socket.on('chat:typing', handleTyping)
  socket.on('chat:read', handleRead)
  socket.on('chat:reaction', handleReaction)
})

onBeforeUnmount(() => {
  if (socket) {
    socket.off('chat:new_message', handleNewMessage)
    socket.off('chat:typing', handleTyping)
    socket.off('chat:read', handleRead)
    socket.off('chat:reaction', handleReaction)
  }
  clearTimeout(typingClearTimer)
})

function formatTime(value) {
  if (!value) return ''
  return new Date(value).toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' })
}
</script>
