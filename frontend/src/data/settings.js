import { ref } from 'vue'

// Shared so the logo menu, the mobile nav item, and the /settings route
// (see router.js) all open the same modal that AppLayout renders.
export const settingsOpen = ref(false)

// The selected modal tab: 'account' or 'saved'. The /settings?tab=saved link
// sets it, so a direct link opens the right tab.
export const settingsTab = ref('account')
