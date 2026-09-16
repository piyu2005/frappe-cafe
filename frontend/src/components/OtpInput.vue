<template>
  <div class="flex gap-2">
    <input
      v-for="(digit, i) in digits"
      :key="i"
      :ref="(el) => (inputs[i] = el)"
      type="text"
      inputmode="numeric"
      autocomplete="one-time-code"
      maxlength="1"
      class="h-12 w-12 rounded-md border border-outline-gray-2 bg-surface-base text-center text-lg-medium text-ink-gray-9 focus:border-outline-gray-4 focus:outline-none"
      :value="digit"
      @input="onInput(i, $event)"
      @keydown="onKeydown(i, $event)"
      @paste="onPaste($event)"
    />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  length: { type: Number, default: 6 },
})
const emit = defineEmits(['update:modelValue', 'complete'])

const inputs = ref([])
const digits = ref(splitValue(props.modelValue))

function splitValue(value) {
  return Array.from({ length: props.length }, (_, i) => value[i] || '')
}

// Covers a parent clearing modelValue back to '' after a failed verify -
// without this, the boxes would keep showing the wrong code the user just
// typed instead of visibly resetting for another attempt.
watch(
  () => props.modelValue,
  (value) => {
    if (value === digits.value.join('')) return
    digits.value = splitValue(value)
  },
)

function emitValue() {
  const value = digits.value.join('')
  emit('update:modelValue', value)
  // Checking the array of individual digits for a gap - unlike the joined
  // string, which trivially "includes" '' no matter its content, so that
  // check alone can never actually detect a still-empty box.
  if (!digits.value.includes('')) {
    emit('complete', value)
  }
}

function onInput(i, event) {
  // Only the last typed character matters - covers both a stray extra
  // keystroke and a single-character paste landing in one box via the
  // browser's own input event instead of a "paste" event.
  const value = event.target.value.replace(/\D/g, '').slice(-1)
  digits.value[i] = value
  event.target.value = value
  emitValue()
  if (value && i < props.length - 1) {
    inputs.value[i + 1]?.focus()
  }
}

function onKeydown(i, event) {
  if (event.key === 'Backspace' && !digits.value[i] && i > 0) {
    inputs.value[i - 1]?.focus()
  }
}

function onPaste(event) {
  event.preventDefault()
  const pasted = (event.clipboardData || window.clipboardData)
    .getData('text')
    .replace(/\D/g, '')
    .slice(0, props.length)
  digits.value = splitValue(pasted)
  emitValue()
  const nextEmpty = digits.value.findIndex((d) => !d)
  inputs.value[nextEmpty === -1 ? props.length - 1 : nextEmpty]?.focus()
}

defineExpose({
  focus: () => inputs.value[0]?.focus(),
})
</script>
