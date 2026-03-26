<template>
  <aside class="fixed left-0 top-0 w-64 h-screen bg-gray-900 border-r border-gray-800 flex flex-col">
    <div class="p-5 border-b border-gray-800">
      <h1 class="text-xl font-bold text-white">RClone Manager</h1>
      <p class="text-xs text-gray-500 mt-1">Cloud Sync Admin</p>
    </div>
    <nav class="flex-1 p-3 space-y-1">
      <NuxtLink
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors"
        :class="$route.path === item.path
          ? 'bg-blue-600/20 text-blue-400'
          : 'text-gray-400 hover:text-white hover:bg-gray-800'"
      >
        <component :is="item.icon" class="w-5 h-5" />
        {{ item.label }}
      </NuxtLink>
    </nav>
    <div class="p-4 border-t border-gray-800">
      <div class="flex items-center gap-2">
        <div class="w-2 h-2 rounded-full" :class="healthOk ? 'bg-green-500' : 'bg-red-500'" />
        <span class="text-xs text-gray-500">rclone {{ healthOk ? 'active' : 'offline' }}</span>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import {
  HomeIcon,
  FolderOpenIcon,
  ArrowPathIcon,
  ClockIcon,
  DocumentTextIcon,
  CogIcon,
} from '@heroicons/vue/24/outline'

const config = useRuntimeConfig()

const navItems = [
  { path: '/', label: 'Dashboard', icon: HomeIcon },
  { path: '/browse', label: 'File Browser', icon: FolderOpenIcon },
  { path: '/tasks', label: 'Sync Tasks', icon: ArrowPathIcon },
  { path: '/logs', label: 'History', icon: DocumentTextIcon },
  { path: '/settings', label: 'Settings', icon: CogIcon },
]

const healthOk = ref(false)

async function checkHealth() {
  try {
    const data = await $fetch<{ rclone: boolean }>(`${config.public.apiBase}/api/health`)
    healthOk.value = data.rclone
  } catch {
    healthOk.value = false
  }
}

onMounted(() => {
  checkHealth()
  setInterval(checkHealth, 10000)
})
</script>
