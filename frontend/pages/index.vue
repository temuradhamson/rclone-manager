<template>
  <div class="space-y-6">
    <!-- Stats cards -->
    <div class="grid grid-cols-4 gap-4">
      <div class="bg-gray-900 rounded-lg border border-gray-800 p-4">
        <p class="text-xs text-gray-500">Total Tasks</p>
        <p class="text-2xl font-bold text-white mt-1">{{ store.tasks.length }}</p>
      </div>
      <div class="bg-gray-900 rounded-lg border border-gray-800 p-4">
        <p class="text-xs text-gray-500">Active Tasks</p>
        <p class="text-2xl font-bold text-green-400 mt-1">{{ activeTasks }}</p>
      </div>
      <div class="bg-gray-900 rounded-lg border border-gray-800 p-4">
        <p class="text-xs text-gray-500">Running Now</p>
        <p class="text-2xl font-bold text-blue-400 mt-1">{{ wsProgress.size }}</p>
      </div>
      <div class="bg-gray-900 rounded-lg border border-gray-800 p-4">
        <p class="text-xs text-gray-500">Remotes</p>
        <p class="text-2xl font-bold text-purple-400 mt-1">{{ remotes.length }}</p>
      </div>
    </div>

    <!-- Weekly transfer summary -->
    <div v-if="weekStats.total_bytes > 0" class="bg-gray-900 rounded-lg border border-gray-800 p-4">
      <div class="flex items-center justify-between">
        <p class="text-xs text-gray-500">Last 7 days</p>
        <NuxtLink to="/stats" class="text-xs text-blue-400 hover:text-blue-300">Details</NuxtLink>
      </div>
      <div class="flex gap-6 mt-2">
        <div>
          <p class="text-lg font-bold text-white">{{ formatSize(weekStats.total_bytes) }}</p>
          <p class="text-[10px] text-gray-500">transferred</p>
        </div>
        <div>
          <p class="text-lg font-bold text-white">{{ formatNumber(weekStats.total_files) }}</p>
          <p class="text-[10px] text-gray-500">files</p>
        </div>
        <div>
          <p class="text-lg font-bold text-white">{{ weekStats.total_syncs }}</p>
          <p class="text-[10px] text-gray-500">syncs</p>
        </div>
        <div v-if="weekStats.total_errors > 0">
          <p class="text-lg font-bold text-red-400">{{ weekStats.total_errors }}</p>
          <p class="text-[10px] text-gray-500">errors</p>
        </div>
      </div>
    </div>

    <!-- Remotes -->
    <div>
      <h3 class="text-sm font-medium text-gray-400 mb-3">Connected Remotes</h3>
      <div class="grid grid-cols-3 gap-4">
        <div
          v-for="remote in remotes"
          :key="remote.name"
          class="bg-gray-900 rounded-lg border border-gray-800 p-4"
        >
          <div class="flex items-center gap-2">
            <CloudIcon class="w-5 h-5" :class="remoteIconColor(remote.type)" />
            <span class="text-white font-medium">{{ remote.name }}</span>
          </div>
          <p class="text-xs text-gray-500 mt-1">{{ remoteLabel(remote.type) }}</p>
          <div v-if="remote.total" class="mt-3">
            <div class="w-full h-1.5 bg-gray-800 rounded-full overflow-hidden">
              <div
                class="h-full transition-all"
                :class="usageColor(remote.used, remote.total)"
                :style="{ width: `${Math.round(((remote.used || 0) / remote.total) * 100)}%` }"
              />
            </div>
            <p class="text-[10px] text-gray-500 mt-1">
              {{ formatSize(remote.used || 0) }} / {{ formatSize(remote.total) }}
              <span class="text-gray-600 ml-1">({{ Math.round(((remote.used || 0) / remote.total) * 100) }}%)</span>
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Recent tasks -->
    <div>
      <div class="flex items-center justify-between mb-3">
        <h3 class="text-sm font-medium text-gray-400">Sync Tasks</h3>
        <NuxtLink to="/browse" class="text-xs text-blue-400 hover:text-blue-300">
          + New Task
        </NuxtLink>
      </div>
      <div class="grid grid-cols-2 gap-3">
        <TasksTaskCard
          v-for="task in store.tasks.slice(0, 6)"
          :key="task.id"
          :task="task"
          :progress-data="wsProgress.get(task.id)"
          @edit="openEdit"
          @run="store.runTask"
          @toggle="store.toggleTask"
          @delete="store.deleteTask"
        />
      </div>
    </div>

    <!-- Edit modal -->
    <TasksTaskModal
      :show="showEditModal"
      :task="editingTask"
      @close="showEditModal = false"
      @saved="onSaved"
    />
  </div>
</template>

<script setup lang="ts">
import { CloudIcon } from '@heroicons/vue/24/outline'

const api = useApi()
const store = useTasksStore()
const { progress: wsProgress, connect } = useRcloneWs()

interface RemoteInfo {
  name: string
  type: string
  total: number | null
  used: number | null
  free: number | null
}

const showEditModal = ref(false)
const editingTask = ref<any>(null)

function openEdit(task: any) {
  editingTask.value = task
  showEditModal.value = true
}

function onSaved() {
  showEditModal.value = false
  store.fetchTasks()
}

const remotes = ref<RemoteInfo[]>([])
const weekStats = ref({ total_bytes: 0, total_files: 0, total_syncs: 0, total_errors: 0 })
const activeTasks = computed(() => store.tasks.filter(t => t.is_enabled).length)

function formatSize(bytes: number): string {
  if (!bytes || bytes <= 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`
}

function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`
  return String(n || 0)
}

function remoteIconColor(type: string): string {
  const colors: Record<string, string> = {
    onedrive: 'text-blue-400',
    drive: 'text-yellow-400',
    s3: 'text-orange-400',
    dropbox: 'text-blue-300',
    local: 'text-gray-400',
  }
  return colors[type] || 'text-purple-400'
}

function remoteLabel(type: string): string {
  const labels: Record<string, string> = {
    onedrive: 'Microsoft OneDrive',
    drive: 'Google Drive',
    s3: 'Amazon S3',
    dropbox: 'Dropbox',
    local: 'Local Filesystem',
  }
  return labels[type] || type
}

function usageColor(used: number | null, total: number): string {
  const pct = ((used || 0) / total) * 100
  if (pct > 90) return 'bg-red-500'
  if (pct > 70) return 'bg-yellow-500'
  return 'bg-blue-500'
}

onMounted(async () => {
  connect()
  await store.fetchTasks()
  try {
    remotes.value = await api.get<RemoteInfo[]>('/api/remotes')
  } catch {}
  try {
    weekStats.value = await api.get('/api/stats/summary', { days: 7 })
  } catch {}
})
</script>
