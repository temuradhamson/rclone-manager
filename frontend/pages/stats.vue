<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h2 class="text-lg font-semibold text-white">Traffic Statistics</h2>
      <select
        v-model="period"
        class="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-gray-300"
      >
        <option :value="7">Last 7 days</option>
        <option :value="14">Last 14 days</option>
        <option :value="30">Last 30 days</option>
        <option :value="90">Last 90 days</option>
      </select>
    </div>

    <!-- Summary cards -->
    <div class="grid grid-cols-4 gap-4">
      <div class="bg-gray-900 rounded-lg border border-gray-800 p-4">
        <p class="text-xs text-gray-500">Total Transferred</p>
        <p class="text-2xl font-bold text-white mt-1">{{ formatSize(summary.total_bytes) }}</p>
      </div>
      <div class="bg-gray-900 rounded-lg border border-gray-800 p-4">
        <p class="text-xs text-gray-500">Files Synced</p>
        <p class="text-2xl font-bold text-blue-400 mt-1">{{ formatNumber(summary.total_files) }}</p>
      </div>
      <div class="bg-gray-900 rounded-lg border border-gray-800 p-4">
        <p class="text-xs text-gray-500">Sync Runs</p>
        <p class="text-2xl font-bold text-green-400 mt-1">{{ summary.total_syncs }}</p>
      </div>
      <div class="bg-gray-900 rounded-lg border border-gray-800 p-4">
        <p class="text-xs text-gray-500">Errors</p>
        <p class="text-2xl font-bold" :class="summary.total_errors > 0 ? 'text-red-400' : 'text-gray-500'">
          {{ summary.total_errors }}
        </p>
      </div>
    </div>

    <!-- Chart -->
    <div class="bg-gray-900 rounded-lg border border-gray-800 p-6">
      <h3 class="text-sm font-medium text-gray-400 mb-4">Daily Transfer Volume</h3>
      <div class="h-64 flex items-end gap-1" v-if="chartData.length">
        <div
          v-for="(day, i) in chartData"
          :key="i"
          class="flex-1 flex flex-col items-center gap-1"
        >
          <div class="w-full flex flex-col justify-end" style="height: 200px">
            <div
              class="w-full bg-blue-500/80 rounded-t transition-all"
              :style="{ height: barHeight(day.downloaded) }"
              :title="`Download: ${formatSize(day.downloaded)}`"
            />
            <div
              class="w-full bg-green-500/80 rounded-t transition-all"
              :style="{ height: barHeight(day.uploaded) }"
              :title="`Upload: ${formatSize(day.uploaded)}`"
            />
          </div>
          <span class="text-[9px] text-gray-600 rotate-[-45deg] origin-center whitespace-nowrap">
            {{ day.date.slice(5) }}
          </span>
        </div>
      </div>
      <div v-else class="h-64 flex items-center justify-center text-gray-600">
        No data for this period
      </div>
      <div class="flex items-center gap-4 mt-4 text-xs text-gray-500">
        <span class="flex items-center gap-1"><span class="w-3 h-3 bg-blue-500/80 rounded" /> Download</span>
        <span class="flex items-center gap-1"><span class="w-3 h-3 bg-green-500/80 rounded" /> Upload</span>
      </div>
    </div>

    <!-- Per-execution table -->
    <div class="bg-gray-900 rounded-lg border border-gray-800 p-6">
      <h3 class="text-sm font-medium text-gray-400 mb-4">Recent Sync History</h3>
      <table class="w-full text-sm">
        <thead>
          <tr class="text-gray-500 text-xs border-b border-gray-800">
            <th class="text-left py-2 font-medium">Task</th>
            <th class="text-left py-2 font-medium">Status</th>
            <th class="text-right py-2 font-medium">Transferred</th>
            <th class="text-right py-2 font-medium">Files</th>
            <th class="text-right py-2 font-medium">Duration</th>
            <th class="text-right py-2 font-medium">Time</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="exec in recentExecs"
            :key="exec.id"
            class="border-b border-gray-800/50 hover:bg-gray-800/30"
          >
            <td class="py-2 text-gray-300">{{ exec.task_name || `Task #${exec.task_id}` }}</td>
            <td class="py-2">
              <span
                class="px-2 py-0.5 rounded text-xs font-medium"
                :class="{
                  'bg-green-900/50 text-green-400': exec.status === 'completed',
                  'bg-red-900/50 text-red-400': exec.status === 'failed',
                  'bg-blue-900/50 text-blue-400': exec.status === 'running',
                }"
              >{{ exec.status }}</span>
            </td>
            <td class="py-2 text-right text-gray-400 font-mono text-xs">{{ formatSize(exec.bytes_transferred || 0) }}</td>
            <td class="py-2 text-right text-gray-400 font-mono text-xs">{{ exec.files_transferred || 0 }}</td>
            <td class="py-2 text-right text-gray-400 font-mono text-xs">{{ formatDuration(exec.duration_seconds) }}</td>
            <td class="py-2 text-right text-gray-500 text-xs">{{ formatTime(exec.started_at) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
const api = useApi()
const period = ref(7)

const summary = ref({ total_bytes: 0, total_files: 0, total_syncs: 0, total_errors: 0 })
const chartData = ref<any[]>([])
const recentExecs = ref<any[]>([])

const maxBytes = computed(() => {
  if (!chartData.value.length) return 1
  return Math.max(...chartData.value.map(d => d.downloaded + d.uploaded), 1)
})

function barHeight(bytes: number): string {
  const pct = (bytes / maxBytes.value) * 100
  return `${Math.max(pct, 0.5)}%`
}

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

function formatDuration(seconds: number | null): string {
  if (!seconds) return '-'
  if (seconds < 60) return `${seconds.toFixed(0)}s`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${Math.floor(seconds % 60)}s`
  return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`
}

function formatTime(iso: string): string {
  if (!iso) return '-'
  const d = new Date(iso)
  return d.toLocaleString('ru-RU', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

async function load() {
  try {
    summary.value = await api.get('/api/stats/summary', { days: period.value })
  } catch {}
  try {
    chartData.value = await api.get('/api/stats/daily', { days: period.value })
  } catch {}
  try {
    const data = await api.get<any>('/api/tasks/executions', { limit: 20 })
    recentExecs.value = data.executions || data || []
  } catch {}
}

watch(period, load)
onMounted(load)
</script>
