<template>
  <div class="max-w-2xl space-y-6">
    <div class="bg-gray-900 rounded-lg border border-gray-800 p-5 space-y-4">
      <h3 class="text-sm font-medium text-white">System Status</h3>
      <div class="grid grid-cols-2 gap-4 text-sm">
        <div>
          <span class="text-gray-500">rclone daemon:</span>
          <span class="ml-2" :class="health?.rclone ? 'text-green-400' : 'text-red-400'">
            {{ health?.rclone ? 'Running' : 'Offline' }}
          </span>
        </div>
        <div>
          <span class="text-gray-500">API:</span>
          <span class="ml-2" :class="health?.status === 'ok' ? 'text-green-400' : 'text-red-400'">
            {{ health?.status || 'Unknown' }}
          </span>
        </div>
      </div>
    </div>

    <div class="bg-gray-900 rounded-lg border border-gray-800 p-5 space-y-4">
      <h3 class="text-sm font-medium text-white">Connected Remotes</h3>
      <div v-for="r in remotes" :key="r.name" class="flex items-center justify-between text-sm py-2 border-b border-gray-800 last:border-0">
        <span class="text-gray-300">{{ r.name }}</span>
        <span class="text-gray-500">{{ r.type }}</span>
      </div>
      <div v-if="remotes.length === 0" class="text-gray-600 text-sm">No remotes configured</div>
    </div>
  </div>
</template>

<script setup lang="ts">
const api = useApi()

const health = ref<{ status: string; rclone: boolean } | null>(null)
const remotes = ref<{ name: string; type: string }[]>([])

onMounted(async () => {
  try {
    health.value = await api.get('/api/health')
  } catch {}
  try {
    remotes.value = await api.get('/api/remotes')
  } catch {}
})
</script>
