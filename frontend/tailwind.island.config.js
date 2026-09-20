import frappeUIPreset from 'frappe-ui/tailwind'

// For the pages that run inside a Builder page (see src/island/). Builder
// already loads a Tailwind reset, so base styles are left out, and only what
// the page uses is scanned. Chosen with the ISLAND environment variable.
const USED_BY = {
  write: ['./src/pages/WritePost.vue', './src/components/StoryPreviewDialog.vue'],
  chat: ['./src/pages/Messages.vue', './src/components/**/*.vue', './src/utils/**/*.js'],
}

/** @type {import('tailwindcss').Config} */
export default {
  presets: [frappeUIPreset],
  corePlugins: { preflight: false },
  content: [
    './src/island/**/*.{vue,js}',
    ...(USED_BY[process.env.ISLAND || 'write'] || []),
    './node_modules/frappe-ui/src/**/*.{vue,js,ts}',
    './node_modules/frappe-ui/frappe/**/*.{vue,js,ts}',
  ],
}
