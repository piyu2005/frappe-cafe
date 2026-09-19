import { ref } from 'vue'

// Shared so the logo menu, the mobile nav item, and the /settings route
// (see router.js) all open the same modal that AppLayout renders.
export const settingsOpen = ref(false)
