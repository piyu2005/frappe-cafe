import { onBeforeUnmount, onMounted, ref } from 'vue'

// Single breakpoint for the whole app's desktop/mobile shell split — anything
// narrower than a small tablet gets the mobile shell (bottom nav, centered
// mobile headers, single-pane chat), matching Tailwind's `md` breakpoint so
// component markup and this check never disagree about where the line is.
const QUERY = '(max-width: 767px)'

// Each caller owns its own matchMedia listener rather than sharing one
// module-level singleton — a shared listener-refcount is exactly the kind of
// mutable module state that can end up out of sync with what's actually
// mounted after enough Vite HMR reloads in a long dev session (a component
// re-running setup() without its old instance's unmount ever firing first).
// A plain per-call listener has no shared state to drift, at the cost of one
// extra matchMedia listener per component using it — a non-issue in practice.
export function useIsMobile() {
  const isMobile = ref(typeof window !== 'undefined' ? window.matchMedia(QUERY).matches : false)

  let mql = null
  function handleChange(e) {
    isMobile.value = e.matches
  }

  onMounted(() => {
    mql = window.matchMedia(QUERY)
    isMobile.value = mql.matches
    mql.addEventListener('change', handleChange)
  })

  onBeforeUnmount(() => {
    mql?.removeEventListener('change', handleChange)
    mql = null
  })

  return isMobile
}
