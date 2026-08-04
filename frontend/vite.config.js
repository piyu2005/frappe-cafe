import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'
import frappeui from 'frappe-ui/vite'

export default defineConfig({
  plugins: [
    frappeui({
      frappeProxy: true,
      lucideIcons: true,
      jinjaBootData: false,
      buildConfig: {
        indexHtmlPath: '../my_new_app/public/frontend/index.html',
      },
    }),
    vue(),
  ],
  server: {
    port: 8080,
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  optimizeDeps: {
    exclude: [
      'frappe-ui',
      // frappe-ui is excluded above (served as source, since it ships raw
      // .vue/.ts and esbuild's optimizer can't process .vue SFCs), but its
      // editor pulls in tiptap/prosemirror from multiple page entry points
      // (WritePost.vue, Messages.vue). Optimizing tiptap separately from
      // frappe-ui's own raw-served imports of it produces two distinct
      // module instances of the same package, which ProseMirror rejects at
      // runtime with "Adding different instances of a keyed plugin". Excluding
      // the whole tiptap graph too keeps it on native, single-instance ESM
      // resolution consistent with frappe-ui's own unbundled imports.
      '@tiptap/core',
      '@tiptap/pm',
      '@tiptap/vue-3',
      '@tiptap/starter-kit',
      '@tiptap/extensions',
      '@tiptap/suggestion',
      '@tiptap/markdown',
    ],
    include: [
      'feather-icons',
      'tippy.js',
      'engine.io-client',
      'socket.io-client',
      'debug',
    ],
  },
})
