<template>
  <Dialog v-model="open" title="Story Preview" size="xl" :dismissible="false">
    <template #default>
      <template v-if="!adjusting">
        <div
          class="group relative w-full overflow-hidden rounded-md bg-surface-gray-2"
          style="aspect-ratio: 1.91"
        >
          <img v-if="previewImageUrl" :src="previewImageUrl" class="size-full object-cover" />
          <div v-else class="flex size-full items-center justify-center text-ink-gray-4">
            <span class="lucide-image size-8" aria-hidden="true" />
          </div>
          <div
            class="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-black/0 opacity-0 transition group-hover:bg-black/40 group-hover:opacity-100"
          >
            <button
              type="button"
              class="rounded-md bg-black/70 px-3 py-1.5 text-sm text-white hover:bg-black/85"
              @click="$emit('change-image')"
            >
              Change preview image
            </button>
            <button
              v-if="previewImageUrl"
              type="button"
              class="rounded-md bg-black/70 px-3 py-1.5 text-sm text-white hover:bg-black/85"
              @click="startAdjusting(previewImageUrl)"
            >
              Adjust image
            </button>
            <button
              v-if="previewImageUrl"
              type="button"
              class="rounded-md bg-black/70 px-3 py-1.5 text-sm text-white hover:bg-black/85"
              @click="$emit('remove-image')"
            >
              Remove image
            </button>
          </div>
        </div>

        <p class="mt-2 text-p-sm text-ink-gray-5">{{ readTime }} min read</p>
        <input
          v-model="titleModel"
          type="text"
          placeholder="Untitled"
          class="mt-2 w-full border-0 border-t border-outline-gray-1 bg-transparent pt-2 text-lg-semibold text-ink-gray-9 placeholder:text-ink-gray-4 focus:outline-none focus:ring-0"
        />
        <textarea
          v-model="excerptModel"
          rows="2"
          placeholder="Write a short preview of your story…"
          class="mt-1 w-full resize-none border-0 border-t border-outline-gray-1 bg-transparent pt-2 text-p-sm text-ink-gray-6 placeholder:text-ink-gray-4 focus:outline-none focus:ring-0"
        />

        <p class="mt-2 text-xs text-ink-gray-4">
          Note: changes here affect how your story appears in previews and feeds — not the story itself.
        </p>
      </template>

      <template v-else>
        <p v-if="canDrag" class="text-p-sm text-ink-gray-6">Drag to reposition.</p>

        <div
          ref="frameRef"
          class="relative mt-3 w-full touch-none select-none overflow-hidden rounded-md bg-black"
          style="aspect-ratio: 1.91"
          :class="canDrag ? 'cursor-move' : 'cursor-default'"
          @mousedown="onDragStart"
          @touchstart="onTouchStart"
        >
          <img
            v-if="imgReady"
            ref="imgRef"
            :src="adjustImageUrl"
            class="absolute"
            :style="{
              width: displayedW + 'px',
              height: displayedH + 'px',
              left: offsetX + 'px',
              top: offsetY + 'px',
            }"
            draggable="false"
          />
        </div>
      </template>
    </template>
    <template #actions>
      <div v-if="!adjusting" class="flex justify-end gap-2">
        <Button variant="outline" label="Cancel" @click="open = false" />
        <Button variant="solid" theme="gray" :label="publishLabel" :loading="publishing" @click="$emit('publish')" />
      </div>
      <div v-else class="flex justify-end gap-2">
        <Button variant="outline" label="Cancel" @click="adjusting = false" />
        <Button variant="solid" theme="gray" label="Done" :loading="savingImage" @click="confirmAdjust" />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { Button, Dialog, useFileUpload } from 'frappe-ui'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  previewImageUrl: { type: String, default: '' },
  readTime: { type: Number, default: 1 },
  publishing: { type: Boolean, default: false },
  publishLabel: { type: String, default: 'Publish' },
})
const emit = defineEmits([
  'publish',
  'change-image',
  'remove-image',
  'update:modelValue',
  'update:previewImageUrl',
])

// Editable in place — title binds straight to the real field; excerpt binds
// to its own override field, same relationship the preview image already
// has with the auto-derived-from-content fallback.
const titleModel = defineModel('title', { default: '' })
const excerptModel = defineModel('excerpt', { default: '' })

const open = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

// Lock page-level pinch/scroll zoom while adjusting so it can't fight with
// our own drag handling.
let restoreViewportContent = null
watch(
  () => open.value && adjusting.value,
  (locked) => {
    const meta = document.querySelector('meta[name="viewport"]')
    if (!meta) return
    if (locked) {
      restoreViewportContent = meta.getAttribute('content')
      meta.setAttribute('content', `${restoreViewportContent}, maximum-scale=1, user-scalable=no`)
    } else if (restoreViewportContent !== null) {
      meta.setAttribute('content', restoreViewportContent)
      restoreViewportContent = null
    }
  },
)


const { upload: uploadFile } = useFileUpload()
const savingImage = ref(false)

const adjusting = ref(false)
const adjustImageUrl = ref('')

const frameRef = ref(null)
const imgRef = ref(null)
const imgReady = ref(false)

const naturalW = ref(0)
const naturalH = ref(0)
const frameW = ref(0)
const frameH = ref(0)
const offsetX = ref(0)
const offsetY = ref(0)

// Fixed at the scale that fills the frame edge-to-edge on the constrained
// axis (no zoom control) — any slack left on the other axis is what dragging
// repositions.
const effectiveScale = computed(() => {
  if (!naturalW.value || !frameW.value) return 1
  return Math.max(frameW.value / naturalW.value, frameH.value / naturalH.value)
})
const displayedW = computed(() => naturalW.value * effectiveScale.value)
const displayedH = computed(() => naturalH.value * effectiveScale.value)
const canDrag = computed(() => displayedW.value > frameW.value + 0.5 || displayedH.value > frameH.value + 0.5)

function centerImage() {
  offsetX.value = (frameW.value - displayedW.value) / 2
  offsetY.value = (frameH.value - displayedH.value) / 2
}

function clampOffset() {
  offsetX.value = displayedW.value <= frameW.value
    ? (frameW.value - displayedW.value) / 2
    : Math.min(0, Math.max(frameW.value - displayedW.value, offsetX.value))
  offsetY.value = displayedH.value <= frameH.value
    ? (frameH.value - displayedH.value) / 2
    : Math.min(0, Math.max(frameH.value - displayedH.value, offsetY.value))
}

function measureFrame() {
  return new Promise((resolve) => {
    if (!frameRef.value) return resolve()
    const observer = new ResizeObserver((entries) => {
      const box = entries[0].contentBoxSize?.[0]
      frameW.value = box ? box.inlineSize : frameRef.value.clientWidth
      frameH.value = box ? box.blockSize : frameRef.value.clientHeight
      observer.disconnect()
      resolve()
    })
    observer.observe(frameRef.value)
  })
}

async function startAdjusting(imageUrl) {
  adjustImageUrl.value = imageUrl
  adjusting.value = true
  imgReady.value = false
  const img = new Image()
  img.src = imageUrl
  await img.decode().catch(() => {})
  naturalW.value = img.naturalWidth || 1
  naturalH.value = img.naturalHeight || 1
  imgReady.value = true
  await nextTick()
  await measureFrame()
  centerImage()
}

let dragging = false
let dragStartX = 0
let dragStartY = 0
let startOffsetX = 0
let startOffsetY = 0

function onDragStart(e) {
  if (!canDrag.value) return
  dragging = true
  dragStartX = e.clientX
  dragStartY = e.clientY
  startOffsetX = offsetX.value
  startOffsetY = offsetY.value
  window.addEventListener('mousemove', onDragMove)
  window.addEventListener('mouseup', onDragEnd)
}

function onDragMove(e) {
  if (!dragging) return
  offsetX.value = startOffsetX + (e.clientX - dragStartX)
  offsetY.value = startOffsetY + (e.clientY - dragStartY)
  clampOffset()
}

function onDragEnd() {
  dragging = false
  window.removeEventListener('mousemove', onDragMove)
  window.removeEventListener('mouseup', onDragEnd)
}

function onTouchStart(e) {
  if (e.touches.length !== 1 || !canDrag.value) return
  dragStartX = e.touches[0].clientX
  dragStartY = e.touches[0].clientY
  startOffsetX = offsetX.value
  startOffsetY = offsetY.value
  window.addEventListener('touchmove', onTouchMove, { passive: false })
  window.addEventListener('touchend', onTouchEnd)
  window.addEventListener('touchcancel', onTouchEnd)
}

function onTouchMove(e) {
  if (e.touches.length !== 1) return
  if (e.cancelable) e.preventDefault()
  offsetX.value = startOffsetX + (e.touches[0].clientX - dragStartX)
  offsetY.value = startOffsetY + (e.touches[0].clientY - dragStartY)
  clampOffset()
}

function onTouchEnd(e) {
  if (e && e.touches && e.touches.length > 0) return
  window.removeEventListener('touchmove', onTouchMove)
  window.removeEventListener('touchend', onTouchEnd)
  window.removeEventListener('touchcancel', onTouchEnd)
}

onBeforeUnmount(() => {
  onDragEnd()
  onTouchEnd()
  if (restoreViewportContent !== null) {
    document.querySelector('meta[name="viewport"]')?.setAttribute('content', restoreViewportContent)
  }
})

async function confirmAdjust() {
  savingImage.value = true
  try {
    const sourceX = -offsetX.value / effectiveScale.value
    const sourceY = -offsetY.value / effectiveScale.value
    const sourceW = frameW.value / effectiveScale.value
    const sourceH = frameH.value / effectiveScale.value

    // Cap at the crop's real pixel resolution — sourceW/H is already in the
    // frame's 1.91 aspect ratio (both derived from the same effectiveScale),
    // so scaling down from it preserves that. Never scale *up* past it: a
    // modest-resolution photo (or a tight crop of one) has fewer real pixels
    // than 1200 to begin with, and stretching those into a fixed 1200-wide
    // canvas is what was making the exported cover image look blurry.
    const outW = Math.round(Math.min(1200, sourceW))
    const outH = Math.round(outW / 1.91)

    const canvas = document.createElement('canvas')
    canvas.width = outW
    canvas.height = outH
    const ctx = canvas.getContext('2d')
    ctx.drawImage(imgRef.value, sourceX, sourceY, sourceW, sourceH, 0, 0, outW, outH)

    const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/jpeg', 0.92))
    const file = new File([blob], 'preview-image.jpg', { type: 'image/jpeg' })
    const result = await uploadFile(file, {})
    emit('update:previewImageUrl', result.file_url)
    adjusting.value = false
  } finally {
    savingImage.value = false
  }
}

defineExpose({ startAdjusting })
</script>
