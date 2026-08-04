<template>
  <PageHeader>
    <Breadcrumbs :items="breadcrumbItems" />
    <div class="flex items-center gap-2">
      <Badge v-if="isEditing" :label="form.status" theme="gray" :variant="statusVariant" />
      <Button
        v-if="form.status !== 'Published'"
        variant="outline"
        theme="gray"
        :label="draftButtonLabel"
        :loading="saving === 'Draft'"
        @click="save('Draft')"
      />
      <Button
        variant="solid"
        theme="gray"
        :label="primaryLabel"
        :loading="saving === 'Published'"
        @click="save('Published')"
      />
      <Dropdown v-if="isEditing" :options="moreOptions">
        <Button icon="lucide-more-horizontal" />
      </Dropdown>
    </div>
  </PageHeader>

  <ScrollArea class="h-[calc(100vh-3rem)]">
    <LoadingText
      v-if="isEditing && existingDoc.loading && !existingDoc.doc"
      class="mx-auto max-w-[770px] px-5 py-8"
      :lines="10"
    />

    <div v-else class="mx-auto max-w-[770px] space-y-5 px-5 py-8">
      <input
        v-model="form.title"
        placeholder="Give your story a title"
        class="w-full border-0 bg-transparent p-0 text-3xl font-semibold text-ink-gray-9 placeholder:text-ink-gray-4 focus:outline-none focus:ring-0"
      />

      <div class="grid grid-cols-2 gap-4">
        <FormControl
          v-model="form.post_type"
          type="select"
          label="Type"
          :options="['Text', 'Blog', 'Image', 'Video']"
        />
        <FormControl
          v-model="form.category"
          type="select"
          label="Category"
          :options="categoryOptions"
        />
      </div>

      <FormControl
        v-if="publications.data && publications.data.length"
        v-model="form.publication"
        type="select"
        label="Publish to"
        :options="[{ label: 'My profile', value: '' }, ...publicationOptions]"
      />

      <div v-if="form.post_type === 'Image' || form.post_type === 'Video'">
        <FormLabel label="Cover" />
        <FileUploader
          class="mt-1.5"
          :file-types="form.post_type === 'Image' ? 'image/*' : 'video/*'"
          @success="onCoverUploaded"
        >
          <template #default="{ uploading, openFileSelector, progress }">
            <Button :loading="uploading" @click="openFileSelector">
              {{ form.attachment ? 'Replace file' : uploading ? `Uploading ${progress}%` : 'Attach file' }}
            </Button>
          </template>
        </FileUploader>

        <div v-if="form.post_type === 'Video' && form.attachment" class="mt-3">
          <p class="text-p-sm text-ink-gray-6">
            Drag the slider to pick a frame, then set it as the cover. The first frame is used by default.
          </p>
          <video
            ref="thumbVideoRef"
            :src="form.attachment"
            class="mt-2 max-h-64 w-full rounded-md border border-outline-gray-1 bg-black object-contain"
            muted
            playsinline
            preload="auto"
            @loadedmetadata="onVideoMetadata"
          />
          <input
            v-if="videoDuration"
            v-model.number="frameTime"
            type="range"
            min="0"
            :max="videoDuration"
            step="0.1"
            class="mt-2 w-full"
            @input="previewFrame"
          />
          <div class="mt-2 flex items-center gap-3">
            <Button size="sm" :loading="generatingThumb" label="Use this frame as cover" @click="captureThumbnail" />
            <div v-if="form.cover_image" class="flex items-center gap-2 text-xs text-ink-gray-5">
              <img :src="form.cover_image" class="h-10 w-16 rounded border border-outline-gray-1 object-cover" />
              Current cover
            </div>
          </div>
          <canvas ref="thumbCanvasRef" class="hidden" />
        </div>
      </div>

      <div>
        <FormLabel label="Content" />
        <Editor
          ref="editorRef"
          v-model="form.content"
          :extensions="extensions"
          :upload-function="uploadFunction"
          placeholder="Write your story…"
        >
          <template #default>
            <div class="mt-1.5 overflow-hidden rounded-lg border border-outline-gray-2 bg-surface-base">
              <EditorBubbleMenu :items="bubbleToolbar" />
              <div class="border-b border-outline-gray-1 px-2 py-1.5">
                <EditorFixedMenu :items="toolbar" class="flex-wrap" />
              </div>
              <EditorContent class="min-h-[420px] px-5 py-4 text-ink-gray-8" />
            </div>
          </template>
        </Editor>
      </div>

      <FormControl v-model="form.tags" label="Tags" placeholder="Design, UX/UI, Minimalism" />

      <ErrorMessage :message="createPost.error?.message || existingDoc.setValue.error?.message" />
    </div>
  </ScrollArea>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Badge,
  Breadcrumbs,
  Button,
  Dropdown,
  ErrorMessage,
  FileUploader,
  FormControl,
  FormLabel,
  LoadingText,
  PageHeader,
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
  FontColor,
  FontHighlight,
  HeadingGroup,
  HorizontalRule,
  InlineCode,
  InsertAttachment,
  InsertIframe,
  InsertImage,
  InsertLink,
  InsertTable,
  InsertVideo,
  Italic,
  OrderedList,
  Redo,
  RichTextKit,
  Separator,
  Strike,
  Undo,
} from 'frappe-ui/editor'
import { ensureHtmlContent } from '@/utils/content'
import { APP_NAME } from '@/utils/appName'

const route = useRoute()
const router = useRouter()

const postId = computed(() => route.params.postId || null)
const isEditing = computed(() => !!postId.value)

const categoryList = useCall({
  url: '/api/v2/method/my_new_app.api.list_categories',
})

const categoryOptions = computed(() => [
  { label: '', value: '' },
  ...(categoryList.data || []).map((c) => ({ label: c.title, value: c.name })),
])

const form = reactive({
  title: '',
  post_type: 'Text',
  category: '',
  content: '',
  attachment: '',
  cover_image: '',
  publication: '',
  tags: '',
  status: 'Draft',
})

const existingDoc = useDoc({
  doctype: 'Post',
  name: () => postId.value || '',
})

watch(
  () => existingDoc.doc,
  (doc) => {
    if (!doc) return
    form.title = doc.title || ''
    form.post_type = doc.post_type || 'Text'
    form.category = doc.category || ''
    form.content = ensureHtmlContent(doc.content)
    form.attachment = doc.attachment || ''
    form.cover_image = doc.cover_image || ''
    form.publication = doc.publication || ''
    form.tags = doc.tags || ''
    form.status = doc.status || 'Draft'
  },
  { immediate: true },
)

const publications = useCall({
  url: '/api/v2/method/my_new_app.api.list_my_publications',
})

const publicationOptions = computed(() =>
  (publications.data || [])
    .filter((p) => p.role === 'Editor')
    .map((p) => ({ label: p.title, value: p.publication })),
)

// Underline is already part of frappe-ui's own StarterKit (on by default),
// which RichTextKit builds on — the toolbar just needs the button below
// (there's no ready-made one), not a second copy of the mark itself.
const extensions = [RichTextKit.configure({ mention: false, tag: false })]

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

const TaskListItem = {
  label: 'Task list',
  icon: 'lucide-list-checks',
  action: (editor) => editor.chain().focus().toggleTaskList().run(),
  isActive: (editor) => editor.isActive('taskList'),
}

const toolbar = [
  Undo,
  Redo,
  Separator,
  HeadingGroup,
  Separator,
  Bold,
  Italic,
  UnderlineItem,
  Strike,
  InlineCode,
  FontColor,
  FontHighlight,
  Separator,
  AlignLeft,
  AlignCenter,
  AlignRight,
  Separator,
  BulletList,
  OrderedList,
  TaskListItem,
  Blockquote,
  Separator,
  InsertLink,
  InsertImage,
  InsertVideo,
  InsertAttachment,
  InsertTable,
  InsertIframe,
  HorizontalRule,
]

const bubbleToolbar = [Bold, Italic, UnderlineItem, Strike, InsertLink, Separator, AlignLeft, AlignCenter, AlignRight]

const { upload: uploadFile } = useFileUpload()

const uploadFunction = async (file) => {
  const result = await uploadFile(file, {})
  return { file_url: result.file_url, file_name: result.file_name }
}

const editorRef = ref(null)

function onCoverUploaded(file) {
  form.attachment = file.file_url
  // Clearing cover_image here lets onVideoMetadata know it should
  // auto-generate a first-frame thumbnail once the new <video> loads.
  form.cover_image = ''
  videoDuration.value = 0
}

const thumbVideoRef = ref(null)
const thumbCanvasRef = ref(null)
const videoDuration = ref(0)
const frameTime = ref(0)
const generatingThumb = ref(false)

function onVideoMetadata() {
  videoDuration.value = thumbVideoRef.value?.duration || 0
  if (!form.cover_image) {
    frameTime.value = Math.min(0.1, videoDuration.value)
    captureThumbnail()
  }
}

function previewFrame() {
  if (thumbVideoRef.value) thumbVideoRef.value.currentTime = frameTime.value
}

function seekTo(video, time) {
  return new Promise((resolve) => {
    function onSeeked() {
      video.removeEventListener('seeked', onSeeked)
      resolve()
    }
    video.addEventListener('seeked', onSeeked)
    video.currentTime = time
  })
}

async function captureThumbnail() {
  const video = thumbVideoRef.value
  const canvas = thumbCanvasRef.value
  if (!video || !canvas) return

  generatingThumb.value = true
  try {
    await seekTo(video, frameTime.value || 0.1)
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height)

    const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/jpeg', 0.85))
    const thumbFile = new File([blob], 'cover.jpg', { type: 'image/jpeg' })
    const result = await uploadFile(thumbFile, {})
    form.cover_image = result.file_url
  } catch (e) {
    toast.error('Could not generate a cover from this video')
  } finally {
    generatingThumb.value = false
  }
}

const breadcrumbItems = computed(() => [
  { label: APP_NAME, route: '/' },
  { label: isEditing.value ? 'Edit' : 'Write' },
])

const statusVariant = computed(() => {
  if (form.status === 'Published') return 'solid'
  if (form.status === 'Archived') return 'subtle'
  return 'outline'
})

const primaryLabel = computed(() => (form.status === 'Published' ? 'Update' : 'Publish'))
const draftButtonLabel = computed(() => (form.status === 'Archived' ? 'Restore to Draft' : 'Save Draft'))

const saving = ref(null)

function handleSaveSuccess(name, targetStatus) {
  saving.value = null
  form.status = targetStatus
  if (targetStatus === 'Published') {
    toast.success('Post published')
    router.push({ name: 'PostDetail', params: { postId: name } })
    return
  }
  toast.success(targetStatus === 'Archived' ? 'Post archived' : 'Draft saved')
  if (!isEditing.value) {
    router.replace({ name: 'WritePost', params: { postId: name } })
  }
}

const createPost = useCall({
  url: '/api/v2/document/Post',
  method: 'POST',
  immediate: false,
  onSuccess(doc) {
    handleSaveSuccess(doc.name, saving.value)
  },
  onError() {
    saving.value = null
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

  saving.value = status
  const payload = { ...form, status }

  if (isEditing.value) {
    existingDoc.setValue
      .submit(payload)
      .then(() => handleSaveSuccess(postId.value, status))
      .catch(() => {
        saving.value = null
      })
  } else {
    createPost.submit(payload)
  }
}

const moreOptions = computed(() => {
  const opts = []
  if (form.status !== 'Archived') {
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
            toast.success('Post deleted')
            router.replace({ name: 'Profile' })
          }),
      }),
  })
  return opts
})
</script>
