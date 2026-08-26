<template>
  <PageHeader v-if="!isMobile">
    <Breadcrumbs :items="breadcrumbItems" />
    <div class="flex items-center gap-2">
      <Button
        variant="outline"
        theme="gray"
        :label="draftButtonLabel"
        :loading="saving === secondaryActionStatus"
        @click="save(secondaryActionStatus)"
      />
      <Button
        variant="solid"
        theme="gray"
        :label="primaryLabel"
        :loading="saving === 'Published'"
        @click="openStoryPreview"
      />
      <Dropdown v-if="isEditing" :options="moreOptions">
        <Button icon="lucide-more-horizontal" />
      </Dropdown>
    </div>
  </PageHeader>
  <PageHeaderMobile v-else :title="isEditing ? 'Edit' : 'Write'">
    <template #left>
      <PageHeaderBackButton :to="isEditing ? { name: 'PostDetail', params: { postId: postId } } : '/'" />
    </template>
    <template #right>
      <div class="flex items-center gap-1">
        <MobileNotificationBell />
        <Dropdown v-if="mobileMoreOptions.length" :options="mobileMoreOptions">
          <Button icon="lucide-more-horizontal" />
        </Dropdown>
        <Button
          variant="solid"
          theme="gray"
          :label="primaryLabel"
          :loading="saving === 'Published'"
          @click="openStoryPreview"
        />
      </div>
    </template>
  </PageHeaderMobile>

  <ScrollArea class="h-full">
    <LoadingText
      v-if="isEditing && existingDoc.loading && !existingDoc.doc"
      class="mx-auto max-w-[770px] px-5 py-8"
      :lines="10"
    />

    <div v-else class="mx-auto max-w-[600px] px-4 py-6 sm:px-0 sm:py-10">
      <p v-if="lastSavedLabel" class="text-center text-sm text-ink-gray-5">
        {{ statusLabel }} · Last saved {{ lastSavedLabel }}
      </p>

      <Editor
        ref="editorRef"
        v-model="form.content"
        :extensions="extensions"
        :upload-function="uploadFunction"
        placeholder="Tell your story…"
      >
        <template #default>
          <div
            class="mt-4 flex max-w-full items-center gap-1 overflow-x-auto rounded-full border border-outline-gray-2 bg-surface-base px-2 py-1 shadow-sm sm:w-fit [&::-webkit-scrollbar]:hidden [scrollbar-width:none]"
          >
            <EditorFixedMenu :items="toolbar" button-size="sm" class="shrink-0" />
          </div>

          <input
            ref="titleInputRef"
            v-model="form.title"
            placeholder="Give your story a title"
            class="mt-4 w-full border-0 bg-transparent p-0 text-p-4xl-semibold text-ink-gray-9 placeholder:text-ink-gray-4 focus:outline-none focus:ring-0"
            @keydown.enter.prevent="focusContentStart"
          />

          <EditorBubbleMenu :items="bubbleToolbar" />
          <EditorContent class="mt-4 min-h-[calc(100vh-320px)] text-ink-gray-8" />
        </template>
      </Editor>

      <FormControl v-model="form.tags" class="mt-8" label="Tags" placeholder="Design, UX/UI, Minimalism" />

      <ErrorMessage :message="createPost.error?.message || existingDoc.setValue.error?.message" />
    </div>
  </ScrollArea>

  <!--
    Kept as a sibling of the dialog, not a descendant inside it — nesting a
    native <input type="file"> inside the Dialog's focus-trapped content
    made the dialog itself auto-dismiss the moment the native OS file picker
    stole focus, kicking the author back out to the write page. Living
    outside the dialog's DOM avoids that entirely.
  -->
  <input ref="storyCoverFileInputRef" type="file" accept="image/*" class="hidden" @change="onStoryCoverFileSelected" />

  <StoryPreviewDialog
    ref="storyPreviewRef"
    v-model="storyPreviewOpen"
    :preview-image-url="previewImageUrl"
    v-model:title="displayTitleForDialog"
    v-model:excerpt="excerptForDialog"
    :read-time="readTime"
    :publishing="saving === 'Published'"
    :publish-label="primaryLabel"
    @change-image="storyCoverFileInputRef?.click()"
    @remove-image="removePreviewImage"
    @update:preview-image-url="onPreviewImageUpdated"
    @publish="confirmPublish"
  />
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Breadcrumbs,
  Button,
  Dropdown,
  ErrorMessage,
  FormControl,
  LoadingText,
  PageHeader,
  PageHeaderBackButton,
  PageHeaderMobile,
  ScrollArea,
  dialog,
  toast,
  useCall,
  useDoc,
  useFileUpload,
} from 'frappe-ui'
import {
  AlignCenter,
  AlignLeft,
  AlignRight,
  Blockquote,
  Bold,
  BulletList,
  Editor,
  EditorBubbleMenu,
  EditorContent,
  EditorFixedMenu,
  HeadingGroup,
  ImageGroup,
  ImageViewer,
  InsertImage,
  InsertLink,
  Italic,
  OrderedList,
  RichTextKit,
  Separator,
  Strike,
} from 'frappe-ui/editor'
import { ensureHtmlContent } from '@/utils/content'
import { APP_NAME } from '@/utils/appName'
import { applyImagePositions, PositionableImage } from '@/utils/positionableImage'
import { useIsMobile } from '@/composables/useIsMobile'

const isMobile = useIsMobile()
import StoryPreviewDialog from '@/components/StoryPreviewDialog.vue'
import MobileNotificationBell from '@/components/MobileNotificationBell.vue'

const route = useRoute()
const router = useRouter()

const postId = computed(() => route.params.postId || null)
const isEditing = computed(() => !!postId.value)

const form = reactive({
  title: '',
  post_type: 'Blog',
  content: '',
  attachment: '',
  images: [],
  cover_image: '',
  excerpt: '',
  display_title: '',
  tags: '',
  status: 'Draft',
})

const existingDoc = useDoc({
  doctype: 'Post',
  name: () => postId.value || '',
})

// Declared before the immediate watch below, which can run synchronously
// during setup (if existingDoc.doc is already populated, e.g. cached from
// an earlier SPA navigation to the same doc) and assigns to it right away.
const lastSavedAt = ref(null)

watch(
  () => existingDoc.doc,
  (doc) => {
    if (!doc) return
    form.title = doc.title || ''
    form.post_type = doc.post_type || 'Blog'
    form.content = ensureHtmlContent(doc.content)
    form.attachment = doc.attachment || ''
    form.images = (doc.images || []).map((row) => ({ image: row.image }))
    form.cover_image = doc.cover_image || ''
    form.excerpt = doc.excerpt || ''
    form.display_title = doc.display_title || ''
    form.tags = doc.tags || ''
    form.status = doc.status || 'Draft'
    lastSavedAt.value = doc.modified ? new Date(doc.modified) : null
  },
  { immediate: true },
)

// The title input doesn't exist in the DOM yet on a fresh mount when editing
// an existing post — it's behind the LoadingText branch until existingDoc
// finishes loading. Watching readiness (rather than focusing once in
// onMounted) covers both the new-post case (ready immediately) and the
// edit case (ready once the doc arrives).
const titleInputRef = ref(null)
const titleReady = computed(() => !isEditing.value || !!existingDoc.doc)
watch(
  titleReady,
  async (ready) => {
    if (!ready) return
    await nextTick()
    titleInputRef.value?.focus()
  },
  { immediate: true },
)

// Enter in the title is a deliberate "done with the title, on to the story"
// signal (Medium does the same) - the title is a single-line <input>, so
// without this Enter would otherwise just do nothing at all.
function focusContentStart() {
  editorRef.value?.editor?.chain().focus('start').run()
}

// "Last saved Xm ago" needs to keep advancing on its own, not just when
// something in `form` happens to change — a light tick is enough to keep it
// honest without recomputing on every keystroke.
const now = ref(Date.now())
let nowInterval = null
onMounted(() => {
  nowInterval = setInterval(() => {
    now.value = Date.now()
  }, 30000)
})
onBeforeUnmount(() => clearInterval(nowInterval))

const statusLabel = computed(() => {
  if (form.status === 'Published') return 'Published'
  if (form.status === 'Archived') return 'Archived'
  return 'Draft'
})

const lastSavedLabel = computed(() => {
  if (!lastSavedAt.value) return null
  const diffSec = Math.floor((now.value - lastSavedAt.value.getTime()) / 1000)
  if (diffSec < 30) return 'just now'
  if (diffSec < 60) return `${diffSec}s ago`
  const diffMin = Math.floor(diffSec / 60)
  if (diffMin < 60) return `${diffMin}m ago`
  const diffHr = Math.floor(diffMin / 60)
  if (diffHr < 24) return `${diffHr}h ago`
  const diffDay = Math.floor(diffHr / 24)
  return `${diffDay}d ago`
})

// Underline is already part of frappe-ui's own StarterKit (on by default),
// which RichTextKit builds on — the toolbar just needs the button below
// (there's no ready-made one), not a second copy of the mark itself.
// `image: false` stops RichTextKit registering its own base Image node, so
// PositionableImage (Image.extend(...), same node name) is the only 'image'
// node in the list — TipTap warns on same-name duplicates otherwise. That
// also skips RichTextKit's own ImageGroup/ImageViewer (they're gated behind
// the same option, since ImageGroup nodes contain Image nodes), so both are
// added back explicitly below — they reference the 'image' node by name,
// not by instance, so they work the same with PositionableImage standing in
// for the base Image node.
// `color: false` — there's no color-picker button in this toolbar, but
// RichTextKit's TextStyle/Color marks are still active by default, which
// means pasting content that carries inline `style="color: ..."` (common
// when pasting from web pages, Google Docs, etc.) makes the pasted text
// render in whatever color the source had, green being a frequent culprit.
// Disabling the marks entirely means pasted text always falls back to the
// editor's own text color, regardless of the source's inline styling.
const extensions = [
  RichTextKit.configure({ mention: false, tag: false, color: false, image: false }),
  PositionableImage,
  ImageGroup,
  ImageViewer,
]

// frappe-ui doesn't ship ready-made toolbar buttons for underline or task
// lists (TaskList/TaskItem are enabled by RichTextKit, just without a menu
// entry), so these follow the same public `CommandMenuItem` shape used to
// build the exported items above — the documented escape hatch for exactly
// this case, not a bypass of it.
const UnderlineItem = {
  label: 'Underline',
  icon: 'lucide-underline',
  action: (editor) => editor.chain().focus().toggleUnderline().run(),
  isActive: (editor) => editor.isActive('underline'),
}

// Trimmed to a compact, always-visible set that fits a floating pill —
// the exhaustive toolbar (undo/redo, colors, tables, attachments, ...)
// doesn't fit the minimal Medium-style redesign, so it's gone from here.
const toolbar = [
  Bold,
  Italic,
  UnderlineItem,
  Strike,
  Separator,
  HeadingGroup,
  Blockquote,
  Separator,
  BulletList,
  OrderedList,
  Separator,
  InsertImage,
  InsertLink,
]

const bubbleToolbar = [Bold, Italic, UnderlineItem, Strike, InsertLink, Separator, AlignLeft, AlignCenter, AlignRight]

const { upload: uploadFile } = useFileUpload()

const uploadFunction = async (file) => {
  const result = await uploadFile(file, {})
  return { file_url: result.file_url, file_name: result.file_name }
}

const editorRef = ref(null)

// When an image/video ends up as the very first block (the common case:
// insert an image before typing anything), there's no paragraph above it to
// click into — clicks near the top of the editor land inside/after the media
// node instead of placing a cursor before it. Keeping a real empty paragraph
// in front of any leading media block gives a stable, clickable line there.
function ensureLeadingParagraph() {
  const editor = editorRef.value?.editor
  if (!editor) return
  const firstNode = editor.state.doc.firstChild
  if (!firstNode) return
  // Media renders as an inline atom *inside* a paragraph, not as its own
  // block sibling — so a leading image ends up as a paragraph whose only
  // content is that atom (no text). With nothing but the atom on that line,
  // there's no unambiguous "before it" position for a click to resolve to.
  // A genuinely separate empty paragraph in front gives a real text line
  // there instead.
  const isLeadingMediaOnly = firstNode.type.name === 'paragraph' && firstNode.textContent === '' && firstNode.content.size > 0
  if (firstNode.type.name !== 'paragraph' || isLeadingMediaOnly) {
    editor.chain().insertContentAt(0, { type: 'paragraph' }).run()
  }
}

// Content images are force-cropped to a fixed box (see the scoped style
// below), so dragging inside that box picks *which part* of the image
// stays visible rather than resizing/moving it — same idea as the cover
// image cropper, applied inline via CSS object-position instead of a
// canvas re-export. Position is stored on the image node itself
// (PositionableImage's objectPosition attribute) so it survives save/
// reload and renders identically on the published post.
function findImageNodePos(editor, imgEl) {
  let foundPos = null
  editor.state.doc.descendants((node, pos) => {
    if (foundPos !== null) return false
    if (node.type.name !== 'image') return
    const dom = editor.view.nodeDOM(pos)
    const nodeImgEl = dom?.querySelector?.('img') || (dom?.tagName === 'IMG' ? dom : null)
    if (nodeImgEl === imgEl) {
      foundPos = pos
      return false
    }
  })
  return foundPos
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value))
}

function parseObjectPosition(el) {
  const raw = el.style.objectPosition || getComputedStyle(el).objectPosition || '50% 50%'
  const [x, y] = raw.split(' ').map((v) => parseFloat(v))
  return { x: Number.isNaN(x) ? 50 : x, y: Number.isNaN(y) ? 50 : y }
}

let dragImg = null
let dragMoved = false
let dragStartX = 0
let dragStartY = 0
let dragStartPos = { x: 50, y: 50 }

function onImageMouseDown(e) {
  const img = e.target.closest?.('.not-prose img')
  if (!img) return
  e.preventDefault()
  dragImg = img
  dragMoved = false
  dragStartX = e.clientX
  dragStartY = e.clientY
  dragStartPos = parseObjectPosition(img)
  img.style.cursor = 'grabbing'
  window.addEventListener('mousemove', onImageMouseMove)
  window.addEventListener('mouseup', onImageMouseUp)
}

function onImageMouseMove(e) {
  if (!dragImg) return
  const dx = e.clientX - dragStartX
  const dy = e.clientY - dragStartY
  if (!dragMoved && (Math.abs(dx) > 3 || Math.abs(dy) > 3)) dragMoved = true
  if (!dragMoved) return
  const rect = dragImg.getBoundingClientRect()
  const newX = clamp(dragStartPos.x + (dx / rect.width) * 100, 0, 100)
  const newY = clamp(dragStartPos.y + (dy / rect.height) * 100, 0, 100)
  dragImg.style.objectPosition = `${newX}% ${newY}%`
}

function onImageMouseUp() {
  window.removeEventListener('mousemove', onImageMouseMove)
  window.removeEventListener('mouseup', onImageMouseUp)
  if (dragImg) {
    dragImg.style.cursor = 'grab'
    if (dragMoved) commitImagePosition(dragImg)
  }
  dragImg = null
  dragMoved = false
}

function commitImagePosition(imgEl) {
  const editor = editorRef.value?.editor
  if (!editor) return
  const pos = findImageNodePos(editor, imgEl)
  if (pos === null) return
  editor.chain().setNodeSelection(pos).updateAttributes('image', { objectPosition: imgEl.style.objectPosition }).run()
}

onMounted(() => {
  const editor = editorRef.value?.editor
  if (editor) editor.on('update', ensureLeadingParagraph)
})

// Reading `editorRef.value?.editor` once inside onMounted and closing over
// it isn't safe here: on the edit-existing-post path, the instance exposed
// by editorRef some ticks later turns out to be a different object than
// whatever onMounted captured (confirmed via direct instance-identity
// checks), so listeners bound to that snapshot never fire against the
// editor actually on screen. Watching the live getter instead re-binds
// against whichever instance is *currently* exposed, and applies any
// positions already stored in the loaded content as soon as it's real.
watch(
  () => editorRef.value?.editor,
  (editor, _old, onCleanup) => {
    if (!editor) return
    const handleUpdate = () => applyImagePositions(editor)
    editor.on('update', handleUpdate)
    // The editor instance exists before its ProseMirror view does —
    // EditorContent mounts the view into the DOM in its own onMounted,
    // which may not have run yet the instant this watcher reacts.
    // `isDestroyed` is false only once a real, live view is mounted (see
    // applyImagePositions's comment for why it's the safe check here, not
    // `.view` itself) — poll a few frames rather than assuming one is enough.
    let attached = false
    let attempts = 0
    function attachDragHandler() {
      if (attached || editor.isDestroyed) return
      editor.view.dom.addEventListener('mousedown', onImageMouseDown)
      attached = true
      applyImagePositions(editor)
    }
    attachDragHandler()
    if (!attached) {
      const poll = () => {
        attempts += 1
        attachDragHandler()
        if (!attached && attempts < 10) requestAnimationFrame(poll)
      }
      requestAnimationFrame(poll)
    }
    onCleanup(() => {
      editor.off('update', handleUpdate)
      if (attached && !editor.isDestroyed) {
        editor.view.dom.removeEventListener('mousedown', onImageMouseDown)
      }
    })
  },
  { immediate: true },
)

onBeforeUnmount(() => {
  window.removeEventListener('mousemove', onImageMouseMove)
  window.removeEventListener('mouseup', onImageMouseUp)
})

// Medium's own behavior: no separate "pick a preview image" step while
// writing — it just uses the first image already in the story, and only
// lets you override/adjust it in the Story Preview step at publish time.
const firstContentImageUrl = computed(() => {
  const match = ensureHtmlContent(form.content).match(/<img[^>]+src="([^"]+)"/)
  return match ? match[1] : ''
})
// Explicit opt-out of a preview image — separate from form.cover_image being
// merely unset, since an unset cover_image still falls back to the first
// content image below. "Removed" means show nothing, full stop, until the
// author picks or adjusts an image again.
const coverImageRemoved = ref(false)
const previewImageUrl = computed(() =>
  coverImageRemoved.value ? '' : form.cover_image || firstContentImageUrl.value,
)

function removePreviewImage() {
  coverImageRemoved.value = true
  form.cover_image = ''
}

function onPreviewImageUpdated(url) {
  coverImageRemoved.value = false
  form.cover_image = url
}

function stripHtml(html) {
  const div = document.createElement('div')
  div.innerHTML = html || ''
  return div.textContent || div.innerText || ''
}

const autoExcerpt = computed(() => {
  const text = stripHtml(ensureHtmlContent(form.content)).trim()
  return text.length > 140 ? text.slice(0, 140) + '…' : text
})
// Same relationship as previewImageUrl/cover_image: shows the auto-derived
// excerpt until the author edits it in the dialog, at which point the edit
// becomes a real, persisted override (form.excerpt) instead.
const excerptForDialog = computed({
  get: () => form.excerpt || autoExcerpt.value,
  set: (value) => {
    form.excerpt = value
  },
})

// Same relationship again, but for the title: editing it in the Story
// Preview dialog only ever touches this separate override, never form.title
// itself — the real story (its heading on the article page, its editor
// field above) is untouched. Falls back to the real title until overridden.
const displayTitleForDialog = computed({
  get: () => form.display_title || form.title,
  set: (value) => {
    form.display_title = value
  },
})

const readTime = computed(() => {
  const words = stripHtml(ensureHtmlContent(form.content)).trim().split(/\s+/).filter(Boolean).length
  return Math.max(1, Math.round(words / 200))
})

const storyPreviewOpen = ref(false)
const storyPreviewRef = ref(null)
const storyCoverFileInputRef = ref(null)

function onStoryCoverFileSelected(e) {
  const file = e.target.files[0]
  if (!file) return
  storyPreviewRef.value?.startAdjusting(URL.createObjectURL(file))
  e.target.value = ''
}

function openStoryPreview() {
  if (editorRef.value?.isEmpty) {
    toast.error('Write something before publishing')
    return
  }
  if (!form.title.trim()) {
    toast.error('Add a title before publishing')
    return
  }
  storyPreviewOpen.value = true
}

function confirmPublish() {
  // previewImageUrl falls back to the first content image only for *display*
  // in the Story Preview dialog — if the author never touched Change/Adjust,
  // form.cover_image itself is still empty. Persist the derived choice now so
  // feed thumbnails (which read cover_image directly) actually have it.
  if (!form.cover_image && previewImageUrl.value) {
    form.cover_image = previewImageUrl.value
  }
  if (!form.excerpt && autoExcerpt.value) {
    form.excerpt = autoExcerpt.value
  }
  save('Published')
}

const breadcrumbItems = computed(() => [
  { label: APP_NAME, route: '/' },
  { label: isEditing.value ? 'Edit' : 'Write' },
])

const primaryLabel = computed(() => (form.status === 'Published' ? 'Update' : 'Publish'))
// Archiving is a one-way trip out of the normal Draft->Published flow, not a
// state to bounce back out of into Draft - an archived post can only be
// edited and re-published, or left archived. The secondary button reflects
// that: for an already-archived post it just re-saves the edits without
// changing its status, it doesn't offer "Restore to Draft" at all.
const secondaryActionStatus = computed(() => (form.status === 'Archived' ? 'Archived' : 'Draft'))
const draftButtonLabel = computed(() => (form.status === 'Archived' ? 'Save' : 'Save Draft'))

const saving = ref(null)
// Set right before createPost.submit() specifically for the fork case (see
// `forkAsNewDraft` in save() below) so its onSuccess can tell "saved a
// genuinely new post" apart from "forked edits off a still-live published
// one" and say so explicitly - the URL silently changing to a different
// post's id would otherwise be a confusing, unexplained surprise.
const savingAsFork = ref(false)

function handleSaveSuccess(name, targetStatus, { isNewDoc = false, isFork = false, previousStatus = null } = {}) {
  saving.value = null
  form.status = targetStatus
  lastSavedAt.value = new Date()
  if (targetStatus === 'Published') {
    toast.success('Post published')
    router.push({ name: 'PostDetail', params: { postId: name } })
    return
  }
  if (isFork) {
    toast.success("Saved as a new draft — your published post wasn't changed")
  } else if (targetStatus === 'Archived') {
    // Same wording either way from the reader's perspective the post just
    // stopped being visible - but re-saving edits to an already-archived
    // post shouldn't claim to have *just* archived it.
    toast.success(previousStatus === 'Archived' ? 'Changes saved' : 'Post archived')
  } else {
    toast.success('Draft saved')
  }
  if (isNewDoc) {
    router.replace({ name: 'WritePost', params: { postId: name } })
  }
}

const createPost = useCall({
  url: '/api/v2/document/Post',
  method: 'POST',
  immediate: false,
  onSuccess(doc) {
    handleSaveSuccess(doc.name, saving.value, { isNewDoc: true, isFork: savingAsFork.value })
    savingAsFork.value = false
  },
  onError() {
    saving.value = null
    savingAsFork.value = false
  },
})

function save(status) {
  if (editorRef.value?.isEmpty) {
    toast.error('Write something before saving')
    return
  }
  if (status === 'Published' && !form.title.trim()) {
    toast.error('Add a title before publishing')
    return
  }

  const previousStatus = form.status
  saving.value = status
  const payload = { ...form, status }

  // Saving a currently-published post as a draft must never touch the live
  // post itself (readers shouldn't see it vanish because someone was just
  // tweaking wording) - fork the edit into a brand-new, independent draft
  // instead. Publishing that draft later is then just publishing its own,
  // separate document - it was never the same row as the original.
  const forkAsNewDraft = isEditing.value && status === 'Draft' && previousStatus === 'Published'

  if (isEditing.value && !forkAsNewDraft) {
    existingDoc.setValue
      .submit(payload)
      .then(() => handleSaveSuccess(postId.value, status, { previousStatus }))
      .catch(() => {
        saving.value = null
      })
  } else {
    savingAsFork.value = forkAsNewDraft
    createPost.submit(payload)
  }
}

const moreOptions = computed(() => {
  const opts = []
  // Archiving only makes sense as a way to take a *live* post down - a
  // draft was never up, so there's nothing to archive it from.
  if (form.status === 'Published') {
    opts.push({ label: 'Archive', icon: 'lucide-archive', onClick: () => save('Archived') })
  }
  opts.push({
    label: 'Delete permanently',
    icon: 'lucide-trash-2',
    onClick: () =>
      dialog.confirm({
        title: 'Delete this post?',
        message: 'This cannot be undone.',
        confirmLabel: 'Delete',
        onConfirm: () =>
          existingDoc.delete.submit().then(() => {
            if (existingDoc.delete.error) {
              toast.error(existingDoc.delete.error.message || 'Failed to delete post')
              return
            }
            toast.success('Post deleted')
            router.replace({ name: 'Profile' })
          }),
      }),
  })
  return opts
})

// Mobile's header only has room for one icon-button's worth of secondary
// actions — folds "Save Draft" (its own always-visible button on desktop) in
// alongside archive/delete rather than dropping it.
const mobileMoreOptions = computed(() => {
  const opts = [
    { label: draftButtonLabel.value, icon: 'lucide-save', onClick: () => save(secondaryActionStatus.value) },
  ]
  if (isEditing.value) opts.push(...moreOptions.value)
  return opts
})
</script>

<style scoped>
/* Mirrors PostDetail.vue's published-view treatment exactly (see its own
   comment for the full rationale) — without this, an inserted image shows
   at its raw natural size while writing, then jumps to a differently-shaped,
   cropped size the moment it's actually posted. Keeping both identical
   makes the editor a true preview of the published result. */
:deep(.not-prose) {
  width: 100% !important;
  height: auto !important;
  aspect-ratio: 16 / 9 !important;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}
:deep(.not-prose > div) {
  height: 100% !important;
}
:deep(.not-prose img),
:deep(.not-prose video) {
  width: 100% !important;
  height: 100% !important;
  object-fit: cover;
}
/* Signals the crop can be repositioned by dragging (see onImageMouseDown) —
   grabbing is set/cleared directly on the element during the drag itself. */
:deep(.not-prose img) {
  cursor: grab;
}
/* The image sits in its own wrapper div carrying the editor's generic `my-2`
   (8px) block spacing — Figma's image blocks use 16px above and below (see
   PostDetail.vue's identical override). */
:deep(div:has(> .not-prose)) {
  margin-top: 16px !important;
  margin-bottom: 16px !important;
}
</style>
