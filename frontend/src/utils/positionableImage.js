import { Image } from 'frappe-ui/editor'

// Extends the base Image node with a persisted `objectPosition` attribute
// (e.g. "30% 70%") so the focal point chosen by dragging an image (see
// WritePost.vue's drag handlers) survives save/reload and renders
// identically on the published post. Same node `name` as the base
// extension it extends, so placing this later in an extensions array
// transparently overrides it — ImageGroup/ImageViewer reference the
// 'image' node by name, not by instance, so they keep working.
export const PositionableImage = Image.extend({
  addAttributes() {
    return {
      ...this.parent?.(),
      objectPosition: {
        default: null,
        parseHTML: (element) =>
          element.style.objectPosition || element.getAttribute('data-object-position') || null,
        renderHTML: (attributes) => {
          if (!attributes.objectPosition) return {}
          return {
            style: `object-position: ${attributes.objectPosition}`,
            'data-object-position': attributes.objectPosition,
          }
        },
      },
    }
  },
})

// frappe-ui's MediaNodeView (the custom NodeView used to actually render
// image nodes while editing/viewing) has no idea this attribute exists —
// its <img> only binds src/alt/width/height, so objectPosition only ever
// reaches the *serialized* HTML (via renderHTML above), never the live DOM
// node. This walks the current document and pushes each image's stored
// position onto its real <img> element directly. MediaNodeView's own
// template never binds `style`, so this survives its re-renders.
export function applyImagePositions(editor) {
  // The editor instance exists before its ProseMirror view is mounted into
  // the DOM (EditorContent does that separately, in its own onMounted), and
  // continues to exist briefly after the view is torn down on unmount — an
  // 'update' can in principle fire in either window. TipTap's `.view`
  // getter doesn't return null/undefined for either case, though — it hands
  // back a Proxy stub that *throws* on touching anything beyond a small
  // safe set (state/dispatch/etc, not nodeDOM). `isDestroyed` is the one
  // getter that's safe to read in both states (true for "not mounted yet"
  // and "already torn down" alike), so it's the guard to use here.
  if (!editor || editor.isDestroyed) return
  editor.state.doc.descendants((node, pos) => {
    if (node.type.name !== 'image' || !node.attrs.objectPosition) return
    const dom = editor.view.nodeDOM(pos)
    const imgEl = dom?.querySelector?.('img') || (dom?.tagName === 'IMG' ? dom : null)
    if (imgEl) imgEl.style.objectPosition = node.attrs.objectPosition
  })
}
