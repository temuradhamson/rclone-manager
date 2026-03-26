<template>
  <div class="space-y-4">
    <div class="bg-gray-900 rounded-lg border border-gray-800 overflow-hidden">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-gray-800 text-gray-500 text-xs">
            <th class="text-left p-3">Task</th>
            <th class="text-left p-3">Status</th>
            <th class="text-left p-3">Trigger</th>
            <th class="text-left p-3">Started</th>
            <th class="text-left p-3">Duration</th>
            <th class="text-right p-3">Transferred</th>
            <th class="text-right p-3">Errors</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="exec in executions"
            :key="exec.id"
            class="border-b border-gray-800/50 hover:bg-gray-800/50"
          >
            <td class="p-3 text-gray-300">#{{ exec.task_id }}</td>
            <td class="p-3">
              <span
                class="px-1.5 py-0.5 rounded text-[10px] font-medium"
                :class="{
                  'bg-green-900/50 text-green-400': exec.status === 'completed',
                  'bg-red-900/50 text-red-400': exec.status === 'failed',
                  'bg-blue-900/50 text-blue-400': exec.status === 'running',
                  'bg-gray-800 text-gray-400': exec.status === 'cancelled',
                }"
              >
                {{ exec.status }}
              </span>
            </td>
            <td class="p-3 text-gray-500">{{ exec.trigger }}</td>
            <td class="p-3 text-gray-400">{{ formatDate(exec.started_at) }}</td>
            <td class="p-3 text-gray-400">{{ formatDuration(exec.duration_seconds) }}</td>
            <td class="p-3 text-right text-gray-400">{{ formatSize(exec.bytes_transferred) }}</td>
            <td class="p-3 text-right" :class="exec.errors_count ? 'text-red-400' : 'text-gray-500'">
              {{ exec.errors_count || 0 }}
            </td>
          </tr>
          <tr v-if="executions.length === 0">
            <td colspan="7" class="p-8 text-center text-gray-600">No executions yet</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
const api = useApi()

interface Execution {
  id: number
  task_id: number | null
  status: string
  trigger: string | null
  started_at: string
  duration_seconds: number | null
  bytes_transferred: number | null
  errors_count: number | null
}

const executions = ref<Execution[]>([])

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString()
}

function formatDuration(sec: number | null): string {
  if (!sec) return '-'
  if (sec < 60) return `${Math.round(sec)}s`
  if (sec < 3600) return `${Math.floor(sec / 60)}m ${Math.round(sec % 60)}s`
  return `${Math.floor(sec / 3600)}h ${Math.floor((sec % 3600) / 60)}m`
}

function formatSize(bytes: number | null): string {
  if (!bytes) return '-'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`
}

onMounted(async () => {
  try {
    executions.value = await api.get<Execution[]>('/api/tasks/executions/list')
  } catch {}
})
</script>
