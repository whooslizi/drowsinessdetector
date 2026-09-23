<script setup lang="ts">
import DrowsinessMonitor from './components/DrowsinessMonitor.vue'
</script>

<template>
  <main class="app-main">
    <DrowsinessMonitor />
  </main>
</template>

<style>
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body, html {
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.app-main {
  width: 100vw;
  height: 100vh;
}
</style>
