import frappeUIPreset from 'frappe-ui/tailwind'

// For the editor that runs inside a Builder page (see src/island/). Builder
// already loads a Tailwind reset, so this leaves its own base styles out and
// only scans what the editor uses.
/** @type {import('tailwindcss').Config} */
export default {
  presets: [frappeUIPreset],
  corePlugins: { preflight: false },
  content: [
    './src/island/**/*.{vue,js}',
    './src/pages/WritePost.vue',
    './src/components/StoryPreviewDialog.vue',
    './node_modules/frappe-ui/src/**/*.{vue,js,ts}',
    './node_modules/frappe-ui/frappe/**/*.{vue,js,ts}',
  ],
}
