<template>
  <header class="h-14 border-b border-gray-800 flex items-center justify-between px-6">
    <h2 class="text-lg font-semibold text-white">{{ title }}</h2>
    <div class="flex items-center gap-4">
      <ProgressMiniBar />
    </div>
  </header>
</template>

<script setup lang="ts">
const route = useRoute()

const titles: Record<string, string> = {
  '/': 'Dashboard',
  '/browse': 'File Browser',
  '/tasks': 'Sync Tasks',
  '/tasks/new': 'New Task',
  '/logs': 'Execution History',
  '/settings': 'Settings',
}

const title = computed(() => titles[route.path] || 'Rclone Manager')
</script>
