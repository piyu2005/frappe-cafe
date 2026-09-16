<template>
  <Tabs
    v-model="tab"
    :tabs="tabs"
    class="settings-tabs"
    :class="{ 'settings-tabs--modal': variant === 'modal' }"
  >
    <template #tab-panel="{ tab: activeTab }">
      <div
        :ref="variant === 'modal' ? (el) => setOuterRef(activeTab.label, el) : undefined"
        :class="variant === 'modal' ? 'settings-modal-scroll-outer' : ''"
      >
        <div
          :ref="variant === 'modal' ? (el) => setPanelRef(activeTab.label, el) : undefined"
          :class="variant === 'modal' ? 'settings-modal-scroll' : ''"
          @scroll="variant === 'modal' ? updateThumb(activeTab.label) : undefined"
        >
        <div v-if="activeTab.label === 'Account'" class="pt-4 divide-y divide-outline-gray-1">
          <div class="flex items-center justify-between py-6">
            <span class="text-base-medium text-ink-gray-8">Username</span>
            <span class="text-sm text-ink-gray-5">@{{ username }}</span>
          </div>
          <div class="flex items-center justify-between py-6">
            <span class="text-base-medium text-ink-gray-8">Email Address</span>
            <span class="text-sm text-ink-gray-5">{{ session.user }}</span>
          </div>
          <div class="flex items-center justify-between py-6">
            <div>
              <div class="text-base-medium text-ink-gray-8">Private account</div>
              <p class="text-sm text-ink-gray-5">
                When on, people must send a follow request to follow you.
              </p>
            </div>
            <Switch v-model="isPrivate" :disabled="updatePrivacy.loading" @update:model-value="handlePrivacyToggle" />
          </div>
          <button
            class="flex w-full items-center justify-between py-6 text-left"
            @click="handleLogout"
          >
            <span class="text-base-medium text-ink-gray-8">Log out</span>
            <span class="lucide-log-out size-4 text-ink-gray-5" aria-hidden="true" />
          </button>
          <div class="flex w-full items-center justify-between py-6 text-left opacity-50">
            <div>
              <span class="text-base-medium text-ink-gray-8">Delete account</span>
              <p class="text-sm text-ink-gray-5">Temporarily unavailable — contact support if you need this.</p>
            </div>
            <span class="lucide-trash-2 size-4 text-ink-gray-5" aria-hidden="true" />
          </div>
        </div>

        <div v-else-if="activeTab.label === 'Saved'" class="pt-4">
          <LoadingText v-if="savedPosts.loading && !savedPosts.data" :lines="4" />
          <p
            v-else-if="savedPosts.data && savedPostsList.length === 0"
            class="text-p-base text-ink-gray-6"
          >
            No saved posts yet.
          </p>
          <div v-else class="divide-y divide-outline-gray-1">
            <div v-for="p in savedPostsList" :key="p.name" class="flex items-center gap-3 py-6">
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
                <img
                  v-if="coverImageFor(p)"
                  :src="coverImageFor(p)"
                  class="h-20 w-24 shrink-0 rounded-md object-cover"
                />
              </router-link>
              <Button
                icon="lucide-bookmark-minus"
                variant="ghost"
                @click="unsave(p.name)"
              />
            </div>
          </div>
        </div>
        </div>
      </div>
      <!-- Teleported to <body>, positioned via fixed viewport coordinates
           computed in the script block - see the comment on
           `.settings-modal-scrollbar-thumb` below for why this can't just
           be position:absolute inside the wrapper above. -->
      <Teleport v-if="variant === 'modal'" to="body">
        <div
          v-if="thumbState[activeTab.label]?.visible"
          class="settings-modal-scrollbar-thumb"
          :style="{
            height: thumbState[activeTab.label].height + 'px',
            top: thumbState[activeTab.label].top + 'px',
            left: thumbState[activeTab.label].left + 'px',
          }"
          @pointerdown="onThumbPointerDown(activeTab.label, $event)"
        />
      </Teleport>
    </template>
  </Tabs>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Button, LoadingText, Switch, Tabs, dialog, toast, useCall } from 'frappe-ui'
import { logout, session } from '@/data/session'

// When embedded in the standalone page (variant: 'page', the default) the
// active tab lives in the URL (?tab=drafts) rather than plain local state -
// clicking into a post navigates away and destroys this component, so a
// local ref alone would always come back on the default "Account" tab when
// the browser's back button returns here. When embedded in the modal
// instead (variant: 'modal'), writing our tab into that unrelated route's
// query would leave a stray ?tab= on whatever page the modal was opened
// from, so it keeps the tab in local state only.
const props = defineProps({
  variant: { type: String, default: 'page' },
})
const emit = defineEmits(['navigate'])

const route = useRoute()
const router = useRouter()

const tabs = [{ label: 'Account' }, { label: 'Saved' }]
const syncRouteQuery = computed(() => props.variant !== 'modal')

function tabIndexFromQuery() {
  if (!syncRouteQuery.value) return 0
  const idx = tabs.findIndex((t) => t.label.toLowerCase() === route.query.tab)
  return idx === -1 ? 0 : idx
}

const tab = ref(tabIndexFromQuery())

watch(tab, (idx) => {
  if (!syncRouteQuery.value) return
  const slug = idx === 0 ? undefined : tabs[idx].label.toLowerCase()
  if ((route.query.tab || undefined) === slug) return
  const query = { ...route.query }
  if (slug) query.tab = slug
  else delete query.tab
  router.replace({ query })
})

// Modal variant only: a hand-rolled scrollbar thumb, kept permanently
// visible whenever a panel actually overflows - unlike either frappe-ui's
// ScrollArea (its track isn't just faded via opacity while idle, reka-ui
// doesn't mount it into the DOM at all until a hover/scroll interaction
// begins) or a plain overflow-y:auto div's native scrollbar (macOS Chrome's
// "automatically based on mouse or trackpad" overlay behavior overrides
// *any* ::-webkit-scrollbar styling, native or custom, the same way).
// Teleported to <body> and positioned via `position: fixed` (viewport
// coordinates read from the panel's own getBoundingClientRect(), not
// position:absolute relative to a wrapper in the normal DOM position) -
// frappe-ui's Dialog wraps every dialog's content in a div with both
// `overflow-hidden` and `transform` (DialogContent's own classes), and a
// transform makes an element the containing block for its
// absolutely-positioned descendants; combined with the sibling
// `overflow-hidden`, a thin child positioned right at that box's edge was
// silently failing to paint at all in testing, in both headless and a real
// browser - teleporting clear of that ancestor chain avoids it entirely.
// Tabs invokes the `#tab-panel` slot once per tab (Account and Saved both,
// not just the active one), so state is keyed by tab label rather than a
// single ref - each panel tracks its own scroll position independently.
const panelEls = {}
const panelOuterEls = {}
const resizeObservers = {}
const thumbState = reactive({
  Account: { visible: false, height: 0, top: 0, left: 0 },
  Saved: { visible: false, height: 0, top: 0, left: 0 },
})

function updateThumb(label) {
  const el = panelEls[label]
  const outer = panelOuterEls[label]
  if (!el || !outer) return
  const { scrollTop, scrollHeight, clientHeight } = el
  const state = thumbState[label]
  const visible = scrollHeight > clientHeight + 1
  state.visible = visible
  if (!visible) return
  const outerRect = outer.getBoundingClientRect()
  const thumbHeight = Math.max((clientHeight / scrollHeight) * clientHeight, 24)
  const maxThumbTop = clientHeight - thumbHeight
  const scrollRange = scrollHeight - clientHeight
  state.height = thumbHeight
  state.top = outerRect.top + (scrollRange > 0 ? (scrollTop / scrollRange) * maxThumbTop : 0)
  // 6px thumb width + 3px gutter from the modal's true edge (outerRect's
  // own right edge already lands there via its negative margin in CSS).
  state.left = outerRect.right - 9
}

function setOuterRef(label, el) {
  panelOuterEls[label] = el
  // Whichever of the two refs (outer wrapper, inner scrollable panel) Vue
  // happens to assign second is the one that can actually compute anything
  // - the other bails out early since its counterpart isn't set yet.
  if (el) updateThumb(label)
}

function setPanelRef(label, el) {
  if (panelEls[label] === el) return
  resizeObservers[label]?.disconnect()
  panelEls[label] = el
  if (!el) return
  updateThumb(label)
  // The scrollable div's own height is fixed - what changes is its
  // *content*'s height (posts loading in, description text wrapping, ...),
  // so the observer watches that first child rather than the div itself.
  const target = el.firstElementChild
  if (!target) return
  const observer = new ResizeObserver(() => updateThumb(label))
  observer.observe(target)
  resizeObservers[label] = observer
}

let thumbDrag = null

function onThumbPointerDown(label, event) {
  const el = panelEls[label]
  const state = thumbState[label]
  if (!el || !state.visible) return
  thumbDrag = {
    label,
    startClientY: event.clientY,
    startScrollTop: el.scrollTop,
    trackHeight: el.clientHeight,
    thumbHeight: state.height,
    scrollRange: el.scrollHeight - el.clientHeight,
  }
  window.addEventListener('pointermove', onThumbPointerMove)
  window.addEventListener('pointerup', onThumbPointerUp)
  event.preventDefault()
  // The thumb is teleported to <body> as a *sibling* of the dialog's real
  // content, not a DOM descendant of it, so reka-ui's own "did this click
  // land outside the dialog?" check (plain DOM containment) reads a click
  // here as outside and closes the dialog. That check runs from a listener
  // on `document`, so stopping propagation here keeps it from ever seeing
  // this pointerdown at all.
  event.stopPropagation()
}

function onThumbPointerMove(event) {
  if (!thumbDrag) return
  const { label, startClientY, startScrollTop, trackHeight, thumbHeight, scrollRange } = thumbDrag
  const el = panelEls[label]
  if (!el) return
  const maxThumbTop = trackHeight - thumbHeight
  if (maxThumbTop <= 0) return
  const deltaScroll = ((event.clientY - startClientY) / maxThumbTop) * scrollRange
  el.scrollTop = Math.min(Math.max(startScrollTop + deltaScroll, 0), scrollRange)
}

function onThumbPointerUp() {
  thumbDrag = null
  window.removeEventListener('pointermove', onThumbPointerMove)
  window.removeEventListener('pointerup', onThumbPointerUp)
}

// The dialog is centered via flex layout, so resizing the window can move
// it without changing either panel's own scroll position - recompute both
// panels' fixed coordinates (not just the active one) so whichever tab the
// reader switches back to already has an up-to-date thumb.
function handleWindowResize() {
  Object.keys(thumbState).forEach(updateThumb)
}
window.addEventListener('resize', handleWindowResize)

onBeforeUnmount(() => {
  Object.values(resizeObservers).forEach((observer) => observer.disconnect())
  window.removeEventListener('resize', handleWindowResize)
  window.removeEventListener('pointermove', onThumbPointerMove)
  window.removeEventListener('pointerup', onThumbPointerUp)
})

const username = computed(() => (session.user || '').split('@')[0])
const isPrivate = ref(false)

const profile = useCall({
  url: '/api/v2/method/my_new_app.api.get_profile',
  params: { user: session.user },
  onSuccess: (data) => {
    isPrivate.value = !!data.is_private
  },
})

const updatePrivacy = useCall({
  url: '/api/v2/method/my_new_app.api.update_profile',
  method: 'POST',
  immediate: false,
  onSuccess: () => toast.success(isPrivate.value ? 'Account is now private' : 'Account is now public'),
  onError: (err) => {
    toast.error(err.message)
    isPrivate.value = !isPrivate.value
  },
})

function handlePrivacyToggle(value) {
  updatePrivacy.submit({ is_private: value ? 1 : 0 })
}

function handleLogout() {
  dialog.confirm({
    title: 'Log out?',
    message: 'You can always log back in.',
    confirmLabel: 'Log out',
    onConfirm: async () => {
      await logout()
      router.replace('/login')
    },
  })
}

const savedPosts = useCall({
  url: '/api/v2/method/my_new_app.api.list_saved_posts',
})

// Removing a post needs to drop it from the list the instant it's clicked,
// before the server confirms — but savedPosts.data is useCall's read-only
// computed, so this keeps its own mutable copy (same pattern as
// PostDetail.vue's commentList) instead of filtering that directly.
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
    // A falsy result means the request failed outright - put the post back.
    // A truthy result where `saved` somehow came back true (a same-post
    // double-click landing between optimistic removal and this response)
    // also means it's still saved - same fix, put it back either way.
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

<style scoped>
/* Tabs' own tablist carries a built-in horizontal px-5, on top of this
   page's container padding — so the tab labels sat further right than the
   content rows below them, which have no padding of their own. Zeroing the
   tablist's own padding (all sides — its `p-1` also added a few px of
   vertical slack) and widening its `gap-5` (20px) to Figma's 32px, and
   shrinking each trigger's own `py-2.5` down to `py-2`, brings the whole bar
   to Figma's exact 33px-tall spec. */
.settings-tabs :deep([role='tablist']) {
  padding: 0;
  gap: 32px;
}
.settings-tabs :deep([role='tab']) {
  padding-top: 8px;
  padding-bottom: 8px;
}

/* Same nested-scrollbar fix as ProfilePosts.vue's own tabs - see that file's
   comment for the full rationale. */
.settings-tabs :deep([role='tabpanel']) {
  overflow: visible;
}

/* Modal variant only: the page can grow/shrink freely since it scrolls with
   the rest of the document, but the Dialog sizes itself to its content, so
   a short tab (e.g. "Saved" with no posts) would shrink the whole modal and
   a long one (many saved posts) would grow it past a sane size. Pinning
   this wrapper to a fixed height and letting the inner panel scroll
   internally keeps the modal itself a constant size either way.
   Two other approaches were tried and dropped before this one: frappe-ui's
   own <ScrollArea> doesn't just fade its thumb via opacity while idle -
   reka-ui doesn't mount it into the DOM at all until a hover/scroll
   interaction begins, so a modal the reader is looking at without having
   moved their pointer into it shows nothing. A plain overflow-y:auto div's
   *native* scrollbar, even with ::-webkit-scrollbar styling, ran into the
   same wall on macOS Chrome - "automatically based on mouse or trackpad"
   (the default) makes the OS apply its own overlay show/hide behavior to
   *any* scrollbar, custom-styled or not. Hand-rendering the thumb as a
   plain positioned div below sidesteps both: nothing about its visibility
   depends on the browser or OS's own scrollbar behavior. */
.settings-modal-scroll-outer {
  position: relative;
  height: 460px;
  /* Dialog's own body wrapper (frappe-ui's Dialog.vue) pads every side with
     px-4 sm:px-6, so the thumb would otherwise sit well inside that padding
     instead of flush against the modal's true edge. Extending past it on
     the right only (negative margin) and adding the same amount back as
     the inner scrollable panel's own padding keeps row content visually
     aligned where it was while the thumb itself lands on the true border. */
  margin-right: -16px;
}

.settings-modal-scroll {
  height: 100%;
  overflow-y: auto;
  padding-right: 16px;
  /* The real scrollbar is hidden entirely (not just unstyled) - our own
     thumb next to it is the only one ever shown. */
  scrollbar-width: none;
}
.settings-modal-scroll::-webkit-scrollbar {
  display: none;
}

@media (min-width: 640px) {
  .settings-modal-scroll-outer {
    margin-right: -24px;
  }
  .settings-modal-scroll {
    padding-right: 24px;
  }
}

/* Styled to match frappe-ui's own ScrollBar thumb (Tabs, ScrollArea, ...):
   ~6px wide, gray-400, fully rounded. `position: fixed` (not absolute) and
   teleported to <body> in the template - see the comment on `thumbState`
   in the script block for why it can't live inside the wrapper above.
   Height/top/left are set inline from the live viewport math there. */
.settings-modal-scrollbar-thumb {
  position: fixed;
  z-index: 60;
  width: 6px;
  border-radius: 9999px;
  background-color: #9ca3af;
  cursor: pointer;
  /* reka-ui's Dialog sets `pointer-events: none` directly on <body> while
     open, to force interaction through the dialog's own content only. That
     content re-enables it on itself, but our thumb - teleported to <body>
     as a *sibling* of the dialog's content, not nested inside it - inherits
     the disabled value instead and needs its own explicit override. */
  pointer-events: auto;
}
</style>
