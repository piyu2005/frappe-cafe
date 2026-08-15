<template>
  <div
    class="relative h-[50vh] min-h-[240px] w-full select-none overflow-hidden rounded-md bg-black sm:h-[420px]"
    @touchstart="onTouchStart"
    @touchend="onTouchEnd"
  >
    <img :src="images[index]" class="size-full object-contain" />

    <template v-if="images.length > 1">
      <span
        class="absolute right-2 top-2 rounded-full bg-black/60 px-2 py-0.5 text-xs text-white"
      >
        {{ index + 1 }}/{{ images.length }}
      </span>

      <button
        type="button"
        class="absolute left-2 top-1/2 flex size-8 -translate-y-1/2 items-center justify-center rounded-full bg-black/50 text-white hover:bg-black/70"
        @click="prev"
      >
        <span class="lucide-chevron-left size-5" aria-hidden="true" />
      </button>
      <button
        type="button"
        class="absolute right-2 top-1/2 flex size-8 -translate-y-1/2 items-center justify-center rounded-full bg-black/50 text-white hover:bg-black/70"
        @click="next"
      >
        <span class="lucide-chevron-right size-5" aria-hidden="true" />
      </button>

      <div class="absolute bottom-2 left-1/2 flex -translate-x-1/2 gap-1.5">
        <button
          v-for="(_, i) in images"
          :key="i"
          type="button"
          class="size-1.5 rounded-full"
          :class="i === index ? 'bg-white' : 'bg-white/50'"
          @click="goTo(i)"
        />
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  images: { type: Array, required: true },
})

const index = ref(0)

function next() {
  index.value = (index.value + 1) % props.images.length
}

function prev() {
  index.value = (index.value - 1 + props.images.length) % props.images.length
}

function goTo(i) {
  index.value = i
}

let touchStartX = 0

function onTouchStart(e) {
  touchStartX = e.changedTouches[0].clientX
}

function onTouchEnd(e) {
  const dx = e.changedTouches[0].clientX - touchStartX
  if (Math.abs(dx) < 40) return
  if (dx < 0) next()
  else prev()
}
</script>
