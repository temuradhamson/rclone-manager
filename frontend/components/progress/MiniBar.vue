<template>
  <div v-if="activeCount > 0" class="flex items-center gap-2 text-sm">
    <div class="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
    <span class="text-gray-400">{{ activeCount }} syncing</span>
  </div>
</template>

<script setup lang="ts">
const { progress } = useRcloneWs()
const activeCount = computed(() => progress.value.size)
</script>
