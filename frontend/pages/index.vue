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
            <CloudIcon class="w-5 h-5 text-blue-400" />
            <span class="text-white font-medium">{{ remote.name }}</span>
          </div>
          <p class="text-xs text-gray-500 mt-1">{{ remote.type }}</p>
          <div v-if="remote.total" class="mt-3">
            <div class="w-full h-1.5 bg-gray-800 rounded-full overflow-hidden">
              <div
                class="h-full bg-blue-500"
                :style="{ width: `${Math.round(((remote.used || 0) / remote.total) * 100)}%` }"
              />
            </div>
            <p class="text-[10px] text-gray-500 mt-1">
              {{ formatSize(remote.used || 0) }} / {{ formatSize(remote.total) }}
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
const activeTasks = computed(() => store.tasks.filter(t => t.is_enabled).length)

function formatSize(bytes: number): string {
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`
}

onMounted(async () => {
  connect()
  await store.fetchTasks()
  try {
    remotes.value = await api.get<RemoteInfo[]>('/api/remotes')
  } catch {}
})
</script>
