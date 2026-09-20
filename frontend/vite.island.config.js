import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'
import frappeui from 'frappe-ui/vite'
import tailwindcss from 'tailwindcss'
import autoprefixer from 'autoprefixer'

// Builder's own stylesheet already loads the Inter font, so this bundle leaves
// its copy out (560 KB).
const dropInterFont = () => ({
  name: 'drop-inter-font',
  enforce: 'post',
  generateBundle(_options, bundle) {
    for (const [file, asset] of Object.entries(bundle)) {
      if (asset.type === 'asset' && file.endsWith('.css')) {
        asset.source = String(asset.source).replace(/@font-face\{[^}]*font-family:(?:InterVar|Inter);[^}]*\}/g, '')
      }
      if (file.startsWith('assets/Inter')) delete bundle[file]
    }
  },
})

// Builds a page of the Vue app into one script and one stylesheet that a
// Builder page loads (see src/island/). ISLAND picks which: write (the post
// editor). Run with: yarn build:write.
const ISLAND = process.env.ISLAND || 'write'
export default defineConfig({
  plugins: [frappeui({ frappeProxy: false, lucideIcons: true, jinjaBootData: false, buildConfig: false }), vue(), dropInterFont()],
  resolve: {
    alias: [
      // The Vue app's own bell opens the Vue notifications panel; the Builder
      // page has its own.
      { find: '@/components/MobileNotificationBell.vue', replacement: path.resolve(__dirname, 'src/island/HostBell.vue') },
      // Live updates and the unread count belong to the Builder page's shell.
      { find: '@/data/socket', replacement: path.resolve(__dirname, 'src/island/socket.js') },
      { find: '@/data/messages', replacement: path.resolve(__dirname, 'src/island/messages.js') },
      { find: '@', replacement: path.resolve(__dirname, 'src') },
    ],
  },
  css: {
    postcss: { plugins: [tailwindcss({ config: './tailwind.island.config.js' }), autoprefixer()] },
  },
  define: { 'process.env.NODE_ENV': JSON.stringify('production') },
  // Not library mode: that inlines every font into the stylesheet (4.5 MB).
  publicDir: false,
  // Where the files are served from; the fonts in the stylesheet are found from here.
  base: `/assets/my_new_app/builder_assets/${ISLAND}/`,
  build: {
    outDir: `../my_new_app/public/builder_assets/${ISLAND}`,
    emptyOutDir: true,
    cssCodeSplit: false,
    rollupOptions: {
      input: path.resolve(__dirname, `src/island/${ISLAND}.js`),
      output: {
        format: 'iife',
        inlineDynamicImports: true,
        entryFileNames: `${ISLAND}.js`,
        assetFileNames: (info) => (info.name && info.name.endsWith('.css') ? `${ISLAND}.css` : 'assets/[name]-[hash][extname]'),
      },
    },
  },
})
