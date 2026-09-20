<template>
  <!-- The Builder page's own bell: notifications.js opens its panel and
       shell.js fills the count. -->
  <span class="mna-host-bell" v-html="markup" />
</template>

<script setup>
import { onMounted } from 'vue'

// Same markup as builder_src/bell.py, for the phone's top bar.
const markup = document.getElementById('mna-bell-template')?.innerHTML || ''

// The page's script filled the counts before this bell existed.
onMounted(() => window.MNA?.refreshBadges?.())
</script>
