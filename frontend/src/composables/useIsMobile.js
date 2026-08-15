import { onBeforeUnmount, onMounted, ref } from 'vue'

// Single breakpoint for the whole app's desktop/mobile shell split — anything
// narrower than a small tablet gets the mobile shell (bottom nav, centered
// mobile headers, single-pane chat), matching Tailwind's `md` breakpoint so
// component markup and this check never disagree about where the line is.
const QUERY = '(max-width: 767px)'

// Module-level singleton: every component calling this shares one
// matchMedia listener instead of each page wiring its own.
const isMobile = ref(typeof window !== 'undefined' ? window.matchMedia(QUERY).matches : false)
let listenerCount = 0
let mql = null

function handleChange(e) {
  isMobile.value = e.matches
}

export function useIsMobile() {
  onMounted(() => {
    if (listenerCount === 0) {
      mql = window.matchMedia(QUERY)
      isMobile.value = mql.matches
      mql.addEventListener('change', handleChange)
    }
    listenerCount++
  })

  onBeforeUnmount(() => {
    listenerCount--
    if (listenerCount === 0 && mql) {
      mql.removeEventListener('change', handleChange)
      mql = null
    }
  })

  return isMobile
}
