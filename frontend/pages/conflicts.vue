<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h2 class="text-lg font-semibold text-white">Bisync Conflicts</h2>
      <button
        @click="scan"
        class="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-500 transition"
        :disabled="scanning"
      >
        {{ scanning ? 'Scanning...' : 'Scan Now' }}
      </button>
    </div>

    <!-- Scan directory input -->
    <div class="bg-gray-900 rounded-lg border border-gray-800 p-4">
      <label class="text-xs text-gray-500 block mb-2">Directory to scan</label>
      <div class="flex gap-3">
        <input
          v-model="scanDir"
          class="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300"
          placeholder="E:\OneDrive"
        />
        <select
          v-model="scanDir"
          class="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300"
        >
          <option value="E:\OneDrive">E:\OneDrive</option>
          <option value="E:\Downloads">E:\Downloads</option>
          <option value="F:\Документы">F:\Документы</option>
        </select>
      </div>
    </div>

    <!-- Results -->
    <div v-if="conflicts.length" class="space-y-2">
      <div class="flex items-center justify-between">
        <p class="text-sm text-gray-400">Found {{ conflicts.length }} conflict(s)</p>
        <button
          @click="resolveAll('delete_conflict')"
          class="px-3 py-1.5 bg-red-600/20 text-red-400 rounded-lg text-xs hover:bg-red-600/30 transition"
        >
          Delete All Conflicts
        </button>
      </div>

      <div
        v-for="(conflict, i) in conflicts"
        :key="i"
        class="bg-gray-900 rounded-lg border border-gray-800 p-4 flex items-center justify-between"
      >
        <div class="flex-1 min-w-0">
          <p class="text-sm text-gray-300 truncate font-mono">{{ conflict.name }}</p>
          <p class="text-xs text-gray-600 truncate mt-0.5">{{ conflict.dir }}</p>
          <div class="flex gap-4 mt-1 text-xs text-gray-500">
            <span>{{ formatSize(conflict.size) }}</span>
            <span>{{ formatDate(conflict.modified) }}</span>
          </div>
        </div>
        <div class="flex gap-2 ml-4">
          <button
            @click="resolve(conflict.path, 'keep_conflict')"
            class="px-3 py-1.5 bg-green-600/20 text-green-400 rounded text-xs hover:bg-green-600/30"
            title="Replace original with conflict version"
          >
            Keep This
          </button>
          <button
            @click="resolve(conflict.path, 'delete_conflict')"
            class="px-3 py-1.5 bg-red-600/20 text-red-400 rounded text-xs hover:bg-red-600/30"
            title="Delete conflict file"
          >
            Delete
          </button>
        </div>
      </div>
    </div>

    <div v-else-if="scanned" class="bg-gray-900 rounded-lg border border-gray-800 p-12 text-center">
      <p class="text-gray-500">No conflicts found</p>
    </div>
  </div>
</template>

<script setup lang="ts">
const api = useApi()

const scanDir = ref('E:\\OneDrive')
const conflicts = ref<any[]>([])
const scanning = ref(false)
const scanned = ref(false)

function formatSize(bytes: number): string {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString('ru-RU', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

async function scan() {
  scanning.value = true
  try {
    const data = await api.get<any>('/api/conflicts', { directory: scanDir.value })
    conflicts.value = data.conflicts || []
    scanned.value = true
  } catch (e) {
    console.error(e)
  } finally {
    scanning.value = false
  }
}

async function resolve(path: string, action: string) {
  try {
    await api.post('/api/conflicts/resolve', { path, action })
    conflicts.value = conflicts.value.filter(c => c.path !== path)
  } catch (e) {
    console.error(e)
  }
}

async function resolveAll(action: string) {
  if (!confirm(`Delete all ${conflicts.value.length} conflict files?`)) return
  for (const c of [...conflicts.value]) {
    await resolve(c.path, action)
  }
}
</script>
