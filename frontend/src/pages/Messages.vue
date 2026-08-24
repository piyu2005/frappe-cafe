<template>
  <PageHeader v-if="!isMobile">
    <Breadcrumbs :items="[{ label: APP_NAME, route: '/' }, { label: 'Messages' }]" />
    <Button
      variant="outline"
      theme="gray"
      icon-left="lucide-users"
      label="New group"
      @click="showCreateGroupDialog = true"
    />
  </PageHeader>
  <!-- On mobile the list and thread are single-pane views, not side-by-side —
       the list is the "root" screen, so it gets the normal mobile header;
       once a conversation is open, the thread's own inline header (below)
       takes over with a back button instead of a second header stacking on
       top of it. -->
  <PageHeaderMobile v-else-if="!activeConversationId" title="Messages">
    <template #right>
      <div class="flex items-center gap-1">
        <MobileNotificationBell />
        <Button variant="outline" theme="gray" icon="lucide-users" @click="showCreateGroupDialog = true" />
      </div>
    </template>
  </PageHeaderMobile>

  <!-- Needs a *definite* height, not h-full: this div sits inside
       DesktopShell's own ScrollArea (default scroll=true), whose content
       wrapper is sized to its content rather than the viewport — h-full
       there just resolves to however tall the content already is, which
       collapsed the whole flex-col (including the composer meant to sit
       flex-pinned at the bottom) down to that same content height. A
       viewport-relative calc sidesteps the ancestor's sizing entirely. -->
  <div class="flex h-[calc(100vh-52px)] md:h-[calc(100vh-3rem)]">
    <!-- Conversation list -->
    <div
      v-if="!isMobile || !activeConversationId"
      class="flex w-full shrink-0 flex-col border-outline-gray-1 md:w-80 md:border-r"
    >
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
              <span v-if="p.username" class="ml-1.5 truncate text-sm text-ink-gray-5">@{{ p.username }}</span>
            </div>
          </button>
        </template>
      </ScrollArea>
    </div>

    <!-- Thread -->
    <div v-if="!isMobile || activeConversationId" class="flex min-w-0 flex-1 flex-col">
      <div v-if="!activeConversationId" class="flex flex-1 items-center justify-center">
        <p class="text-p-base text-ink-gray-5">Select a conversation to start messaging.</p>
      </div>

      <template v-else-if="conversation.data">
        <div class="flex items-center justify-between border-b border-outline-gray-1 px-3 py-3 sm:px-4">
          <div class="flex min-w-0 items-center gap-1 sm:gap-3">
            <button
              v-if="isMobile"
              type="button"
              class="flex size-8 shrink-0 items-center justify-center rounded text-ink-gray-6 hover:bg-surface-gray-2"
              @click="router.push({ name: 'Messages' })"
            >
              <span class="lucide-arrow-left size-5" aria-hidden="true" />
            </button>
            <Avatar :image="conversation.data.display_image" :label="conversation.data.display_name" size="md" />
            <div class="min-w-0">
              <router-link
                v-if="conversation.data.other_user"
                :to="{ name: 'Profile', params: { userId: conversation.data.other_user } }"
                class="block truncate text-base-medium text-ink-gray-9 hover:underline"
              >
                {{ conversation.data.display_name }}
              </router-link>
              <div v-else class="truncate text-base-medium text-ink-gray-9">{{ conversation.data.display_name }}</div>
              <div v-if="typingUser" class="text-xs text-ink-gray-5">typing…</div>
            </div>
          </div>
          <div class="flex shrink-0 items-center gap-2">
            <button class="text-ink-gray-5 hover:text-ink-gray-9" @click="searchOpen = !searchOpen">
              <span class="lucide-search size-4" aria-hidden="true" />
            </button>
            <Dropdown :options="threadOptions">
              <Button icon="lucide-more-horizontal" />
            </Dropdown>
          </div>
        </div>

        <div v-if="searchOpen" class="border-b border-outline-gray-1 p-3">
          <TextInput
            ref="messageSearchInputRef"
            v-model="messageSearchQuery"
            placeholder="Search in this conversation"
            @input="onSearchInput"
          />
          <div v-if="searchResults.data && searchResults.data.length" class="mt-2 space-y-1">
            <button
              v-for="r in searchResults.data"
              :key="r.name"
              type="button"
              class="block w-full rounded px-2 py-1 text-left text-sm text-ink-gray-7 hover:bg-surface-gray-1"
              @click="jumpToMessage(r.name)"
            >
              <span class="font-medium text-ink-gray-9">{{ r.sender_name }}:</span> {{ r.content }}
            </button>
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
              :data-message-id="m.name"
              class="group flex items-end gap-2"
              :class="m.sender === session.user ? 'flex-row-reverse' : ''"
            >
              <Avatar v-if="m.sender !== session.user" :image="m.sender_image" :label="m.sender_name" size="sm" />
              <!-- The 70% cap is for open-ended text; a multi-image grid is a
                   fixed, deterministic width (2 columns of size-28 + gap —
                   see the grid below), so it's given `w-fit` with no percent
                   cap instead. Capping it too would re-trigger the very
                   problem this fixes: `fit-content` on a box wrapping a
                   flex-wrap descendant doesn't "discover" the descendant's
                   natural post-wrap width — it clamps to whatever ambient
                   width is offered (here, 70% of the row), and if that
                   happens to land narrower than two columns' width, the
                   grid re-wraps down to one column instead of rendering at
                   its intended fixed size. -->
              <div :class="imageAttachments(m).length > 1 ? 'w-fit' : 'max-w-[70%]'">
                <div
                  class="relative rounded-lg bg-surface-gray-2 px-3 py-2 text-sm text-ink-gray-9 transition-colors duration-500"
                  :class="highlightedMessageId === m.name ? 'bg-surface-amber-2' : ''"
                >
                  <div v-if="m.is_deleted" class="italic text-ink-gray-5">This message was deleted</div>

                  <template v-else>
                  <button
                    v-if="m.reply_to_preview"
                    type="button"
                    class="mb-1.5 block w-full rounded border-l-2 border-outline-gray-4 bg-black/5 px-2 py-1 text-left"
                    @click="jumpToMessage(m.reply_to_preview.name)"
                  >
                    <div class="truncate text-xs font-medium text-ink-gray-7">{{ m.reply_to_preview.sender_name }}</div>
                    <div class="truncate text-xs text-ink-gray-5">
                      {{ m.reply_to_preview.is_deleted ? 'This message was deleted' : m.reply_to_preview.content }}
                    </div>
                  </button>

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
                  <!-- A committed w-[230px] (2 × size-28 + one gap-1.5), not
                       max-w — an ambient/percentage-derived width here is
                       exactly what caused the wrap to collapse to one column
                       (see the wrapper's comment above); a fixed width makes
                       the 2-column wrap unconditional. -->
                  <div
                    v-if="m.attachments && m.attachments.length"
                    class="mt-1 flex flex-wrap gap-1.5"
                    :class="imageAttachments(m).length > 1 ? 'w-[230px]' : ''"
                  >
                    <button
                      v-for="(a, i) in imageAttachments(m).slice(0, IMAGE_PREVIEW_LIMIT)"
                      :key="'img-' + i"
                      type="button"
                      class="relative overflow-hidden rounded"
                      :class="imageAttachments(m).length > 1 ? 'size-28' : ''"
                      @click="openLightbox(m, i)"
                    >
                      <img
                        :src="a.file_url"
                        class="rounded object-cover"
                        :class="imageAttachments(m).length > 1 ? 'size-full' : 'max-h-64'"
                      />
                      <div
                        v-if="i === IMAGE_PREVIEW_LIMIT - 1 && hiddenImageCount(m) > 0"
                        class="absolute inset-0 flex items-center justify-center rounded bg-black/50 text-lg font-medium text-white"
                      >
                        +{{ hiddenImageCount(m) }}
                      </div>
                    </button>
                    <a
                      v-for="(a, i) in fileAttachments(m)"
                      :key="'file-' + i"
                      :href="a.file_url"
                      target="_blank"
                      rel="noopener"
                      class="flex items-center gap-2 rounded-lg border border-outline-gray-2 bg-surface-base px-2 py-1.5 text-xs text-ink-gray-8 no-underline hover:bg-surface-gray-1"
                    >
                      <span class="lucide-file size-3.5 shrink-0 text-ink-gray-5" aria-hidden="true" />
                      <span class="max-w-32 truncate">{{ a.file_name }}</span>
                    </a>
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

                  <div v-if="m.poll_data" class="mt-2 w-72 rounded-lg border border-outline-gray-2 bg-surface-base p-3">
                    <div class="text-sm-medium text-ink-gray-9">{{ m.poll_data.question }}</div>
                    <div class="mt-2.5 flex flex-col gap-1.5">
                      <button
                        v-for="opt in m.poll_data.options"
                        :key="opt.name"
                        type="button"
                        class="relative w-full overflow-hidden rounded-md border border-outline-gray-2 px-2.5 py-1.5 text-left text-sm disabled:cursor-default"
                        :disabled="m.poll_data.is_closed"
                        @click="votePollOption(m, opt)"
                      >
                        <div
                          class="absolute inset-y-0 left-0 bg-surface-gray-2"
                          :style="{ width: pollOptionPercent(m.poll_data, opt) + '%' }"
                          aria-hidden="true"
                        />
                        <div class="relative flex items-center justify-between gap-2">
                          <span class="flex items-center gap-1.5 text-ink-gray-8">
                            <span
                              :class="opt.voted_by_me ? 'lucide-check-circle-2' : 'lucide-circle text-ink-gray-4'"
                              class="size-3.5 shrink-0"
                              aria-hidden="true"
                            />
                            {{ opt.option_text }}
                          </span>
                          <span class="shrink-0 text-xs text-ink-gray-5">{{ opt.vote_count }}</span>
                        </div>
                      </button>
                    </div>
                    <div class="mt-2 flex items-center gap-1.5 text-xs text-ink-gray-5">
                      <span>{{ m.poll_data.total_votes }} {{ m.poll_data.total_votes === 1 ? 'vote' : 'votes' }}</span>
                      <span v-if="m.poll_data.allow_multiple">· Multiple choice</span>
                      <span v-if="m.poll_data.is_closed">· Closed</span>
                    </div>
                  </div>

                  <Popover>
                    <template #trigger="{ isOpen }">
                      <button
                        class="absolute -top-3 size-6 items-center justify-center rounded-full border border-outline-gray-1 bg-surface-base text-ink-gray-6"
                        :class="[
                          m.sender === session.user ? '-left-3' : '-right-3',
                          // Once open, stay visible regardless of :hover on .group — the
                          // popover panel is teleported to <body>, so it visually overlaps
                          // this button without being its DOM descendant. If visibility
                          // still depended on group-hover, moving the mouse from the tiny
                          // trigger into the (larger, higher z-index) panel would cover
                          // .group at that screen point, dropping :hover on it — hiding
                          // this button, collapsing its layout box, and yanking the
                          // floating position out from under the open panel. That's the
                          // flicker/jump: hide -> reposition -> mouse lands back over
                          // .group -> show -> reposition again, repeating.
                          isOpen ? 'flex' : 'hidden group-hover:flex',
                        ]"
                      >
                        <span class="lucide-smile-plus size-3.5" aria-hidden="true" />
                      </button>
                    </template>
                    <template #default="{ close }">
                      <EmojiPicker @select="(e) => (toggleReaction(m.name, e), close())" />
                    </template>
                  </Popover>

                  <button
                    type="button"
                    class="absolute -top-3 size-6 items-center justify-center rounded-full border border-outline-gray-1 bg-surface-base text-ink-gray-6"
                    :class="[m.sender === session.user ? '-left-10' : '-right-10', 'hidden group-hover:flex']"
                    @click="startReply(m)"
                  >
                    <span class="lucide-reply size-3.5" aria-hidden="true" />
                  </button>

                  <Dropdown v-if="m.sender === session.user" :options="messageOptions(m)" placement="right">
                    <template #default="{ open }">
                      <button
                        type="button"
                        class="absolute -top-3 -left-16 size-6 items-center justify-center rounded-full border border-outline-gray-1 bg-surface-base text-ink-gray-6"
                        :class="open ? 'flex' : 'hidden group-hover:flex'"
                      >
                        <span class="lucide-more-horizontal size-3.5" aria-hidden="true" />
                      </button>
                    </template>
                  </Dropdown>
                  </template>
                </div>

                <div v-if="!m.is_deleted && m.reactions && m.reactions.length" class="mt-1 flex flex-wrap gap-1" :class="m.sender === session.user ? 'justify-end' : ''">
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
                  {{ formatTime(m.creation) }}<span v-if="m.is_edited && !m.is_deleted"> · edited</span>
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
                <div
                  v-if="replyingTo || editingMessage"
                  class="flex items-center justify-between gap-2 border-b border-outline-gray-1 px-3 py-2"
                >
                  <div class="min-w-0 flex-1">
                    <div class="text-xs font-medium text-ink-gray-7">
                      {{ editingMessage ? 'Editing message' : `Replying to ${replyingTo.sender_name}` }}
                    </div>
                    <div v-if="replyingTo" class="truncate text-xs text-ink-gray-5">
                      {{ messagePreviewText(replyingTo) }}
                    </div>
                  </div>
                  <button
                    type="button"
                    class="flex size-6 shrink-0 items-center justify-center rounded text-ink-gray-5 hover:bg-surface-gray-2 hover:text-ink-gray-8"
                    @click="editingMessage ? cancelEdit() : cancelReply()"
                  >
                    <span class="lucide-x size-3.5" aria-hidden="true" />
                  </button>
                </div>

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
                  @paste="onComposerPaste"
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
                              :disabled="uploading || conversation.data.is_blocked || !!editingMessage"
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
                          @click="insertMentionTrigger"
                        >
                          <span class="lucide-at-sign size-4" aria-hidden="true" />
                        </button>
                      </Tooltip>

                      <Popover>
                        <template #trigger>
                          <button
                            type="button"
                            title="Emoji"
                            class="flex size-7 items-center justify-center rounded text-ink-gray-5 hover:bg-surface-gray-2 hover:text-ink-gray-8 disabled:opacity-50"
                            :disabled="conversation.data.is_blocked"
                          >
                            <span class="lucide-smile-plus size-4" aria-hidden="true" />
                          </button>
                        </template>
                        <template #default="{ close }">
                          <EmojiPicker @select="(e) => (selectEmoji(e), close())" />
                        </template>
                      </Popover>

                      <span class="mx-1 h-4 w-px bg-outline-gray-2" aria-hidden="true" />

                      <Tooltip text="Poll">
                        <button
                          type="button"
                          class="flex size-7 items-center justify-center rounded text-ink-gray-5 hover:bg-surface-gray-2 hover:text-ink-gray-8 disabled:opacity-50"
                          :disabled="conversation.data.is_blocked || !!editingMessage"
                          @click="openPollDialog"
                        >
                          <span class="lucide-bar-chart-2 size-4" aria-hidden="true" />
                        </button>
                      </Tooltip>
                    </div>
                  </TooltipProvider>
                  <Button
                    variant="solid"
                    theme="gray"
                    :icon="editingMessage ? 'lucide-check' : 'lucide-send'"
                    :loading="editingMessage ? editMessageCall.loading : sendMessage.loading"
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

    <Dialog v-model:open="showPollDialog" size="lg" title="Create Poll">
      <template #default>
        <div class="flex flex-col gap-5">
          <FormControl
            v-model="pollQuestion"
            type="textarea"
            label="Question"
            placeholder="What would you like to ask?"
            :rows="2"
          />

          <div>
            <span class="mb-1.5 block text-sm-medium text-ink-gray-7">Options</span>
            <div class="flex flex-col gap-2">
              <div v-for="(option, i) in pollOptions" :key="i" class="flex items-center gap-2">
                <TextInput v-model="pollOptions[i]" :placeholder="`Option ${i + 1}`" class="flex-1" />
                <Button
                  v-if="pollOptions.length > 2"
                  variant="ghost"
                  icon="lucide-x"
                  @click="removePollOption(i)"
                />
              </div>
            </div>
            <Button class="mt-2 !text-ink-gray-5" variant="ghost" label="Add option" @click="addPollOption">
              <template #prefix>
                <span class="lucide-plus size-4" aria-hidden="true" />
              </template>
            </Button>
          </div>

          <div class="border-t border-outline-gray-1 pt-4">
            <span class="mb-3 block text-sm-medium text-ink-gray-7">Poll Settings</span>
            <div class="flex flex-col gap-4">
              <Switch
                v-model="pollAllowMultiple"
                label="Allow multiple choices"
                description="Voters can select more than one option"
              />
              <Switch
                v-model="pollAnonymous"
                label="Anonymous poll"
                description="Hide voter identities from other participants"
              />
              <Switch
                v-model="pollCloseEnabled"
                label="Close this poll automatically"
                description="Stop accepting votes at a chosen date and time"
              />
              <FormControl v-if="pollCloseEnabled" v-model="pollCloseAt" type="datetime" label="Close at" />
            </div>
          </div>
        </div>
      </template>
      <template #actions="{ close }">
        <div class="flex justify-end gap-2">
          <Button variant="outline" label="Cancel" @click="close" />
          <Button
            variant="solid"
            theme="gray"
            label="Create Poll"
            :loading="createPoll.loading"
            :disabled="!canCreatePoll"
            @click="submitPoll"
          />
        </div>
      </template>
    </Dialog>

    <CreateGroupDialog v-model="showCreateGroupDialog" @created="onGroupCreated" />

    <GroupMembersDialog
      v-if="conversation.data?.is_group"
      v-model="showGroupMembersDialog"
      :conversation="activeConversationId"
      :group-title="conversation.data.display_name"
      @renamed="onGroupRenamed"
      @left="conversations.reload()"
    />

    <Teleport to="body">
      <div
        v-if="lightboxOpen"
        class="fixed inset-0 z-[100] flex items-center justify-center bg-black/90"
        @click.self="closeLightbox"
      >
        <button
          type="button"
          class="absolute right-4 top-4 flex size-9 items-center justify-center rounded-full bg-white/10 text-white hover:bg-white/20"
          @click="closeLightbox"
        >
          <span class="lucide-x size-5" aria-hidden="true" />
        </button>

        <a
          v-if="currentLightboxImage"
          :href="currentLightboxImage.file_url"
          :download="currentLightboxImage.file_name || ''"
          class="absolute right-16 top-4 flex size-9 items-center justify-center rounded-full bg-white/10 text-white hover:bg-white/20"
        >
          <span class="lucide-download size-5" aria-hidden="true" />
        </a>

        <button
          v-if="lightboxImages.length > 1"
          type="button"
          class="absolute left-4 top-1/2 flex size-9 -translate-y-1/2 items-center justify-center rounded-full bg-white/10 text-white hover:bg-white/20"
          @click.stop="prevLightboxImage"
        >
          <span class="lucide-chevron-left size-5" aria-hidden="true" />
        </button>
        <button
          v-if="lightboxImages.length > 1"
          type="button"
          class="absolute right-4 top-1/2 flex size-9 -translate-y-1/2 items-center justify-center rounded-full bg-white/10 text-white hover:bg-white/20"
          @click.stop="nextLightboxImage"
        >
          <span class="lucide-chevron-right size-5" aria-hidden="true" />
        </button>

        <img
          v-if="currentLightboxImage"
          :src="currentLightboxImage.file_url"
          class="max-h-[90vh] max-w-[90vw] object-contain"
          @click.stop
        />

        <div
          v-if="lightboxImages.length > 1"
          class="absolute bottom-4 left-1/2 -translate-x-1/2 text-sm text-white/80"
        >
          {{ lightboxIndex + 1 }} / {{ lightboxImages.length }}
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Avatar,
  Breadcrumbs,
  Button,
  Dialog,
  Dropdown,
  FileUploader,
  FormControl,
  LoadingText,
  PageHeader,
  PageHeaderMobile,
  Popover,
  ScrollArea,
  Switch,
  TextInput,
  Tooltip,
  TooltipProvider,
  dialog,
  formatBytes,
  toast,
  useCall,
  useFileUpload,
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
import { useIsMobile } from '@/composables/useIsMobile'
import EmojiPicker from '@/components/EmojiPicker.vue'
import MobileNotificationBell from '@/components/MobileNotificationBell.vue'

const isMobile = useIsMobile()
import MentionChip from '@/components/MentionChip.vue'
import CreateGroupDialog from '@/components/CreateGroupDialog.vue'
import GroupMembersDialog from '@/components/GroupMembersDialog.vue'

const route = useRoute()
const router = useRouter()

const search = ref('')
const newMessageText = ref('')
const pendingAttachments = ref([])
const typingUser = ref(null)
const searchOpen = ref(false)
const messageSearchQuery = ref('')
const messageSearchInputRef = ref(null)

watch(searchOpen, async (open) => {
  if (!open) return
  await nextTick()
  messageSearchInputRef.value?.el?.focus()
})
const highlightedMessageId = ref(null)
const replyingTo = ref(null)
const editingMessage = ref(null)
const scrollAreaRef = ref(null)
const composerEditorRef = ref(null)
const fileUploaderRef = ref(null)
const showFormatting = ref(false)
const showPollDialog = ref(false)
const pollQuestion = ref('')
const pollOptions = ref(['', ''])
const pollAllowMultiple = ref(false)
const pollAnonymous = ref(false)
const pollCloseEnabled = ref(false)
const pollCloseAt = ref('')

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

const activeConversationId = computed(() => route.params.conversationId || null)

const mentionableUsers = useCall({
  url: '/api/v2/method/my_new_app.chat.list_mentionable_users',
  params: () => ({ conversation: activeConversationId.value }),
  immediate: false,
})

// `items` accepts a ref/getter and is read live at suggestion-time (see
// frappe-ui's mention extension), so this can just be handed to
// CommentKit.configure() below without re-triggering it manually.
const mentionCandidates = computed(() =>
  (mentionableUsers.data || []).map((u) => ({
    id: u.name,
    // @-mentions read as handles, not display names — username first, only
    // falling back when a user hasn't set one.
    label: u.username || u.full_name || u.name,
    value: u.name,
    email: u.name,
    full_name: u.full_name,
  })),
)

// CommentKit ("comments, chat, replies" per frappe-ui) is the lighter stack
// vs RichTextKit — no headings/tables/task-lists. Media/tag/emoji are
// disabled since this app attaches files and picks emoji through its own UI
// below, not the editor's built-in nodes. Mention stays on, rendered through
// MentionChip so hovering a mention (in the composer or in past messages —
// both share this same extension list) shows a profile card with a way to
// message that person, not just plain "@username" text. Underline is
// already part of frappe-ui's own StarterKit (on by default), so it just
// needs the toolbar button above. Highlight isn't part of CommentKit's
// defaults, so it's added here directly — both are pulled in only through
// `frappe-ui/editor`'s own exports, never a direct `@tiptap/*` import (see
// vite.config.js's optimizeDeps comment for why that matters).
const composerExtensions = [
  CommentKit.configure({
    mention: { items: mentionCandidates, component: MentionChip },
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

// Used for the "Replying to …" preview above the composer, where the source
// is a full message from messageList (possibly rich-text HTML) rather than
// the already-plain-text reply_to_preview the backend sends with each
// message — that one is rendered as-is in the message bubble.
function messagePreviewText(m) {
  if (!m) return ''
  if (m.is_deleted) return 'This message was deleted'
  if (m.content) return isHtmlContent(m.content) ? m.content.replace(/<[^>]+>/g, ' ').trim() : m.content
  if (m.attachments && m.attachments.length) return 'Attachment'
  if (m.shared_post) return 'Shared post'
  if (m.poll_data) return 'Poll'
  return ''
}

let typingClearTimer = null
let typingThrottled = false

const conversations = useCall({
  url: '/api/v2/method/my_new_app.chat.list_conversations',
  refetch: true,
})

const conversation = useCall({
  url: '/api/v2/method/my_new_app.chat.get_conversation',
  params: () => ({ conversation: activeConversationId.value }),
  immediate: false,
})

// Bumped past the backend's default 50 only when jumping to a search result
// older than what's currently loaded (see jumpToMessage) — reset on every
// conversation switch so a normal open doesn't fetch more than it needs.
const messagesFetchLimit = ref(50)

const messages = useCall({
  url: '/api/v2/method/my_new_app.chat.get_messages',
  params: () => ({ conversation: activeConversationId.value, limit: messagesFetchLimit.value }),
  immediate: false,
})

// useCall's `.data` is a read-only computed (no setter) — keep our own
// mutable copy so realtime events / optimistic updates can push into it.
// Unlike PostDetail.vue's comment list, `messages.reload()` here only ever
// runs when switching conversations (see openConversationData) — clearing to
// `[]` on the transient null is deliberate: it's what lets the loading
// skeleton show instead of the previous conversation's messages lingering
// under the new conversation's header.
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

// A search hit previously did nothing when clicked — jump back to the real
// message in the thread and flash it briefly so it's obvious which one
// matched. The backend only loads the most recent 50 messages by default,
// so an older hit won't be in the DOM yet; pull in more history once and
// retry before giving up.
async function jumpToMessage(messageId) {
  searchOpen.value = false
  await nextTick()

  const findEl = () => scrollAreaRef.value?.$el?.querySelector(`[data-message-id="${messageId}"]`)

  let el = findEl()
  if (!el) {
    messagesFetchLimit.value += 200
    await messages.reload()
    await nextTick()
    el = findEl()
  }
  if (!el) {
    toast.error("Couldn't find that message")
    return
  }

  el.scrollIntoView({ behavior: 'smooth', block: 'center' })
  highlightedMessageId.value = messageId
  setTimeout(() => {
    if (highlightedMessageId.value === messageId) highlightedMessageId.value = null
  }, 1500)
}

async function openConversationData(id) {
  typingUser.value = null
  searchOpen.value = false
  messageSearchQuery.value = ''
  messagesFetchLimit.value = 50
  replyingTo.value = null
  editingMessage.value = null
  if (!id) return
  await Promise.all([conversation.reload(), messages.reload(), mentionableUsers.reload()])
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

const showCreateGroupDialog = ref(false)
const showGroupMembersDialog = ref(false)

function onGroupCreated(conversationId) {
  conversations.reload()
  openConversation(conversationId)
}

function onGroupRenamed() {
  conversation.reload()
  conversations.reload()
}

const sendMessage = useCall({
  url: '/api/v2/method/my_new_app.chat.send_message',
  method: 'POST',
  immediate: false,
  onError: (err) => toast.error(err.message),
})

// Own messages never show sender_name/sender_image (see the template's
// `v-if="m.sender !== session.user"` on the avatar) - so a placeholder needs
// no real profile fetch, unlike PostDetail.vue's optimistic comments, which
// stay inline in a shared list and do need to show a name.
let tempMessageSeq = 0
function buildOptimisticMessage({ content, attachments, replyTo }) {
  tempMessageSeq += 1
  return {
    name: `temp-${Date.now()}-${tempMessageSeq}`,
    sender: session.user,
    sender_name: null,
    sender_image: null,
    content,
    reply_to: replyTo?.name || null,
    reply_to_preview: replyTo
      ? {
          name: replyTo.name,
          sender_name: replyTo.sender_name,
          content: messagePreviewText(replyTo),
          is_deleted: replyTo.is_deleted ? 1 : 0,
        }
      : null,
    is_edited: 0,
    is_deleted: 0,
    attachments,
    shared_post: null,
    poll: null,
    poll_data: null,
    link_url: null,
    link_title: null,
    link_description: null,
    link_image: null,
    creation: new Date().toISOString(),
    reactions: [],
  }
}

const editMessageCall = useCall({
  url: '/api/v2/method/my_new_app.chat.edit_message',
  method: 'POST',
  immediate: false,
  onSuccess: (result) => {
    const target = messageList.value.find((m) => m.name === editingMessage.value?.name)
    if (target) {
      target.content = result.content
      target.is_edited = result.is_edited
    }
    cancelEdit()
  },
  onError: (err) => toast.error(err.message),
})

function startReply(m) {
  editingMessage.value = null
  replyingTo.value = m
  composerEditorRef.value?.editor?.chain().focus().run()
}

function cancelReply() {
  replyingTo.value = null
}

// Content is applied via editor.commands.setContent() rather than just
// setting the newMessageText ref: the Editor's internal v-model watcher skips
// re-applying a value that matches the *last value it emitted*, to avoid
// bouncing a user's own keystroke back through setContent. Since the message
// being edited was typically typed in this same composer moments earlier,
// its content usually still matches that last-emitted value one-for-one — so
// setting the ref alone silently no-ops and leaves the composer looking
// empty. Calling setContent() directly bypasses that guard entirely.
function startEdit(m) {
  replyingTo.value = null
  editingMessage.value = m
  nextTick(() => {
    const editor = composerEditorRef.value?.editor
    editor?.commands.setContent(m.content || '')
    editor?.chain().focus('end').run()
  })
}

function cancelEdit() {
  editingMessage.value = null
  composerEditorRef.value?.editor?.commands.setContent('')
}

function messageOptions(m) {
  return [
    { label: 'Edit', icon: 'lucide-pencil', onClick: () => startEdit(m) },
    { label: 'Delete', icon: 'lucide-trash-2', onClick: () => confirmDeleteMessage(m) },
  ]
}

const deleteMessageCall = useCall({
  url: '/api/v2/method/my_new_app.chat.delete_message',
  method: 'POST',
  immediate: false,
  onSuccess: () => {
    markMessageDeletedLocally(deleteMessageCall.params?.message)
    conversations.reload()
  },
  onError: (err) => toast.error(err.message),
})

function markMessageDeletedLocally(messageId) {
  const target = messageList.value.find((m) => m.name === messageId)
  if (!target) return
  target.is_deleted = 1
  target.content = null
  target.attachments = []
  target.shared_post = null
  target.poll = null
  target.poll_data = null
  target.link_url = null
  target.link_title = null
  target.link_description = null
  target.link_image = null
  target.reactions = []
}

function confirmDeleteMessage(m) {
  dialog.confirm({
    title: 'Delete message?',
    message: "This can't be undone. This message will be removed for everyone in this conversation.",
    theme: 'red',
    confirmLabel: 'Delete',
    onConfirm: () => deleteMessageCall.submit({ message: m.name }),
  })
}

function submitMessage() {
  const editor = composerEditorRef.value?.editor
  const isEmpty = !editor || editor.isEmpty

  if (editingMessage.value) {
    if (isEmpty) return
    editMessageCall.submit({ message: editingMessage.value.name, content: newMessageText.value })
    return
  }

  if ((isEmpty && !pendingAttachments.value.length) || !activeConversationId.value) return

  const content = isEmpty ? null : newMessageText.value
  const attachmentsPayload = pendingAttachments.value.map((a) => ({
    file_url: a.file_url,
    file_name: a.file_name,
    file_size: a.file_size,
  }))
  const replyTo = replyingTo.value
  const conversationId = activeConversationId.value

  const optimistic = buildOptimisticMessage({ content, attachments: attachmentsPayload, replyTo })
  messageList.value = [...messageList.value, optimistic]
  newMessageText.value = ''
  pendingAttachments.value = []
  replyingTo.value = null
  scrollToBottom()

  sendMessage
    .submit({
      conversation: conversationId,
      content,
      attachments: attachmentsPayload,
      reply_to: replyTo?.name || null,
    })
    .then((result) => {
      const idx = messageList.value.findIndex((m) => m.name === optimistic.name)
      if (idx === -1) return
      if (result) {
        // Swap the placeholder for the server-confirmed message in place,
        // same idea as PostDetail.vue's optimistic comments - keeps its
        // position rather than a reload reshuffling the whole list.
        const updated = [...messageList.value]
        updated[idx] = result
        messageList.value = updated
        conversations.reload()
      } else {
        // Failed - drop the placeholder and hand everything back so nothing
        // typed is lost. Restoring via editor.commands.setContent() rather
        // than just the newMessageText ref: the Editor's v-model watcher
        // skips re-applying a value that matches the *last value it
        // emitted* (see startEdit's comment above for the full mechanism),
        // and the content being restored here is exactly what was last
        // typed - setting the ref alone would silently no-op and leave the
        // composer looking empty even though newMessageText itself is
        // correct.
        messageList.value = messageList.value.filter((m) => m.name !== optimistic.name)
        if (content) composerEditorRef.value?.editor?.commands.setContent(content)
        pendingAttachments.value = attachmentsPayload
        replyingTo.value = replyTo
      }
    })
}

function isImageFile(fileName) {
  return /\.(jpe?g|png|gif|webp)$/i.test(fileName || '')
}

// A message with many images shouldn't blow up the bubble to full-screen —
// show the first few and fold the rest behind a "+N" badge on the last one,
// the same convention as most chat apps' image-grid overflow.
const IMAGE_PREVIEW_LIMIT = 4

function imageAttachments(m) {
  return (m.attachments || []).filter((a) => isImageFile(a.file_name))
}

function fileAttachments(m) {
  return (m.attachments || []).filter((a) => !isImageFile(a.file_name))
}

function hiddenImageCount(m) {
  return Math.max(0, imageAttachments(m).length - IMAGE_PREVIEW_LIMIT)
}

// Clicking a thumbnail previously did nothing — open a full-screen viewer
// with the *entire* set of images from that message (not just the capped
// preview), so browsing past the "+N" overflow works via the arrows too.
const lightboxOpen = ref(false)
const lightboxImages = ref([])
const lightboxIndex = ref(0)
const currentLightboxImage = computed(() => lightboxImages.value[lightboxIndex.value] || null)

function openLightbox(m, index) {
  lightboxImages.value = imageAttachments(m)
  lightboxIndex.value = index
  lightboxOpen.value = true
}

function closeLightbox() {
  lightboxOpen.value = false
}

function nextLightboxImage() {
  lightboxIndex.value = (lightboxIndex.value + 1) % lightboxImages.value.length
}

function prevLightboxImage() {
  lightboxIndex.value = (lightboxIndex.value - 1 + lightboxImages.value.length) % lightboxImages.value.length
}

function onLightboxKeydown(e) {
  if (!lightboxOpen.value) return
  if (e.key === 'Escape') closeLightbox()
  else if (e.key === 'ArrowRight') nextLightboxImage()
  else if (e.key === 'ArrowLeft') prevLightboxImage()
}

onMounted(() => window.addEventListener('keydown', onLightboxKeydown))
onBeforeUnmount(() => window.removeEventListener('keydown', onLightboxKeydown))

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

// Screenshots/copied images arrive as clipboard files, not text — same
// upload path as the paperclip button (FileUploader), just without a file
// picker in between. Only image items are intercepted; a plain text paste
// (the common case) is left alone to fall through to the editor's own
// default handling.
const { upload: uploadPastedFile } = useFileUpload()

async function onComposerPaste(event) {
  if (conversation.data?.is_blocked) return

  const items = Array.from(event.clipboardData?.items || [])
  const imageItems = items.filter((item) => item.kind === 'file' && item.type.startsWith('image/'))
  if (!imageItems.length) return

  event.preventDefault()
  for (const item of imageItems) {
    const file = item.getAsFile()
    if (!file) continue
    try {
      const uploaded = await uploadPastedFile(file, { private: true })
      onFileUploaded(uploaded)
    } catch (err) {
      toast.error(err?.message || 'Error uploading image')
    }
  }
}

function clearPendingAttachment(index) {
  pendingAttachments.value = pendingAttachments.value.filter((_, i) => i !== index)
}

const canCreatePoll = computed(
  () => pollQuestion.value.trim() && pollOptions.value.filter((o) => o.trim()).length >= 2,
)

function openPollDialog() {
  pollQuestion.value = ''
  pollOptions.value = ['', '']
  pollAllowMultiple.value = false
  pollAnonymous.value = false
  pollCloseEnabled.value = false
  pollCloseAt.value = ''
  showPollDialog.value = true
}

function addPollOption() {
  pollOptions.value = [...pollOptions.value, '']
}

function removePollOption(index) {
  pollOptions.value = pollOptions.value.filter((_, i) => i !== index)
}

const createPoll = useCall({
  url: '/api/v2/method/my_new_app.chat.create_poll',
  method: 'POST',
  immediate: false,
  onSuccess: (msg) => {
    messageList.value = [...messageList.value, msg]
    showPollDialog.value = false
    conversations.reload()
    scrollToBottom()
  },
  onError: (err) => toast.error(err.message),
})

function submitPoll() {
  if (!canCreatePoll.value || !activeConversationId.value) return
  createPoll.submit({
    conversation: activeConversationId.value,
    question: pollQuestion.value,
    options: pollOptions.value.filter((o) => o.trim()),
    allow_multiple: pollAllowMultiple.value ? 1 : 0,
    anonymous: pollAnonymous.value ? 1 : 0,
    close_at: pollCloseEnabled.value && pollCloseAt.value ? pollCloseAt.value : null,
  })
}

const votePoll = useCall({
  url: '/api/v2/method/my_new_app.chat.toggle_poll_vote',
  method: 'POST',
  immediate: false,
  onError: (err) => toast.error(err.message),
})

// Mirrors toggle_poll_vote's own logic (chat.py): unvoting removes exactly
// one vote from the clicked option; voting adds one - and for a single-
// choice poll, also removes whatever other option this user had previously
// voted for, netting zero change to total_votes rather than +1.
function withToggledVote(pollData, optionName) {
  const clicked = pollData.options.find((o) => o.name === optionName)
  if (!clicked) return pollData
  const wasVoted = clicked.voted_by_me
  const previousVote = pollData.allow_multiple
    ? null
    : pollData.options.find((o) => o.name !== optionName && o.voted_by_me)

  let totalDelta = 0
  const options = pollData.options.map((o) => {
    if (o.name === optionName) {
      totalDelta += wasVoted ? -1 : 1
      return { ...o, voted_by_me: !wasVoted, vote_count: o.vote_count + (wasVoted ? -1 : 1) }
    }
    if (previousVote && o.name === previousVote.name) {
      totalDelta -= 1
      return { ...o, voted_by_me: false, vote_count: Math.max(0, o.vote_count - 1) }
    }
    return o
  })

  return { ...pollData, options, total_votes: pollData.total_votes + totalDelta }
}

function votePollOption(message, option) {
  if (message.poll_data?.is_closed) return
  const target = messageList.value.find((m) => m.name === message.name)
  if (!target?.poll_data) return
  const previousPollData = target.poll_data
  target.poll_data = withToggledVote(previousPollData, option.name)

  votePoll.submit({ option: option.name }).then((result) => {
    if (result) {
      target.poll_data = result
    } else {
      target.poll_data = previousPollData
    }
  })
}

function pollOptionPercent(pollData, option) {
  if (!pollData.total_votes) return 0
  return Math.round((option.vote_count / pollData.total_votes) * 100)
}

const setTypingCall = useCall({
  url: '/api/v2/method/my_new_app.chat.set_typing',
  method: 'POST',
  immediate: false,
})

function selectEmoji(e) {
  composerEditorRef.value?.editor?.chain().focus().insertContent(e).run()
}

// Same trigger a typed "@" would produce — the suggestion plugin matches on
// document content, not the keystroke itself, so inserting the character
// opens the same popup. Like typing it manually, this only fires when "@"
// ends up preceded by whitespace/start-of-line; mid-word it's just a literal
// "@", same as the keyboard would give you.
function insertMentionTrigger() {
  composerEditorRef.value?.editor?.chain().focus().insertContent('@').run()
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
})

// Flips the tapped emoji's count/reacted_by_me the same way the backend's
// _group_reactions would - used to show the change immediately, before the
// server confirms it.
function withToggledReaction(reactions, emoji) {
  const existing = reactions.find((r) => r.emoji === emoji)
  if (existing?.reacted_by_me) {
    if (existing.count <= 1) return reactions.filter((r) => r.emoji !== emoji)
    return reactions.map((r) => (r.emoji === emoji ? { ...r, count: r.count - 1, reacted_by_me: false } : r))
  }
  if (existing) {
    return reactions.map((r) => (r.emoji === emoji ? { ...r, count: r.count + 1, reacted_by_me: true } : r))
  }
  return [...reactions, { emoji, count: 1, reacted_by_me: true }]
}

function toggleReaction(message, emoji) {
  const msg = messageList.value.find((m) => m.name === message)
  if (!msg) return
  const previousReactions = msg.reactions
  msg.reactions = withToggledReaction(previousReactions, emoji)

  toggleReactionCall.submit({ message, emoji }).then((result) => {
    if (result) {
      msg.reactions = result
    } else {
      msg.reactions = previousReactions
    }
  })
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
  const opts = []
  if (conversation.data.is_group) {
    opts.push({
      label: 'Group info',
      icon: 'lucide-users',
      onClick: () => (showGroupMembersDialog.value = true),
    })
  }
  opts.push({
    label: conversation.data.muted ? 'Unmute' : 'Mute',
    icon: conversation.data.muted ? 'lucide-bell' : 'lucide-bell-off',
    onClick: () =>
      muteCall.submit({ conversation: activeConversationId.value, muted: conversation.data.muted ? 0 : 1 }),
  })
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

function handlePollUpdate(payload) {
  const msg = messageList.value.find((m) => m.name === payload.message)
  if (msg) msg.poll_data = payload.poll_data
}

function handleMessageEdited(payload) {
  const msg = messageList.value.find((m) => m.name === payload.message)
  if (msg) {
    msg.content = payload.content
    msg.is_edited = payload.is_edited
  }
}

function handleMessageDeleted(payload) {
  markMessageDeletedLocally(payload.message)
  conversations.reload()
}

let socket = null
onMounted(() => {
  socket = getSocket()
  socket.on('chat:new_message', handleNewMessage)
  socket.on('chat:typing', handleTyping)
  socket.on('chat:read', handleRead)
  socket.on('chat:reaction', handleReaction)
  socket.on('chat:poll_update', handlePollUpdate)
  socket.on('chat:message_edited', handleMessageEdited)
  socket.on('chat:message_deleted', handleMessageDeleted)
})

onBeforeUnmount(() => {
  if (socket) {
    socket.off('chat:new_message', handleNewMessage)
    socket.off('chat:typing', handleTyping)
    socket.off('chat:read', handleRead)
    socket.off('chat:reaction', handleReaction)
    socket.off('chat:poll_update', handlePollUpdate)
    socket.off('chat:message_edited', handleMessageEdited)
    socket.off('chat:message_deleted', handleMessageDeleted)
  }
  clearTimeout(typingClearTimer)
})

function formatTime(value) {
  if (!value) return ''
  return new Date(value).toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' })
}
</script>
