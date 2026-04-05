<template>
  <div class="bg-gray-900 rounded-lg border border-gray-800 p-4 hover:border-gray-700 transition-colors">
    <div class="flex items-start justify-between">
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2">
          <h3 class="text-sm font-medium text-white truncate">{{ task.name }}</h3>
          <span
            class="px-1.5 py-0.5 text-[10px] rounded font-medium"
            :class="task.is_enabled ? 'bg-green-900/50 text-green-400' : 'bg-gray-800 text-gray-500'"
          >
            {{ task.is_enabled ? 'ON' : 'OFF' }}
          </span>
        </div>
        <p v-if="task.description" class="text-xs text-gray-500 mt-1 truncate">{{ task.description }}</p>
      </div>
      <div class="flex items-center gap-1 ml-2">
        <button
          class="p-1.5 rounded hover:bg-gray-800 text-gray-400 hover:text-blue-400 transition-colors"
          title="Edit"
          @click="$emit('edit', task)"
        >
          <PencilSquareIcon class="w-4 h-4" />
        </button>
        <button
          class="p-1.5 rounded hover:bg-gray-800 text-gray-400 hover:text-green-400 transition-colors"
          title="Run now"
          @click="$emit('run', task.id)"
        >
          <PlayIcon class="w-4 h-4" />
        </button>
        <button
          class="p-1.5 rounded hover:bg-gray-800 text-gray-400 hover:text-yellow-400 transition-colors"
          title="Toggle"
          @click="$emit('toggle', task.id)"
        >
          <PauseIcon class="w-4 h-4" />
        </button>
        <button
          class="p-1.5 rounded hover:bg-gray-800 text-gray-400 hover:text-red-400 transition-colors"
          title="Delete"
          @click="$emit('delete', task.id)"
        >
          <TrashIcon class="w-4 h-4" />
        </button>
      </div>
    </div>

    <!-- Paths -->
    <div class="mt-3 flex items-center gap-2 text-xs">
      <span class="text-gray-400 truncate max-w-[40%]">{{ task.src_path }}</span>
      <ArrowRightIcon class="w-3 h-3 text-gray-600 shrink-0" />
      <span class="text-gray-400 truncate max-w-[40%]">{{ task.dst_path }}</span>
    </div>

    <!-- Mode badge + schedule -->
    <div class="mt-2 flex items-center gap-2 flex-wrap">
      <span class="px-2 py-0.5 bg-blue-900/30 text-blue-400 text-[10px] rounded-full">
        {{ modeLabel }}
      </span>
      <span
        v-if="schedule"
        class="px-2 py-0.5 text-[10px] rounded-full"
        :class="schedule.is_active ? 'bg-purple-900/30 text-purple-400' : 'bg-gray-800 text-gray-500'"
      >
        {{ scheduleLabel }}
      </span>
      <button
        @click="showSchedule = !showSchedule"
        class="px-2 py-0.5 bg-gray-800 text-gray-500 text-[10px] rounded-full hover:text-gray-300 transition"
      >
        {{ schedule ? 'Edit Schedule' : '+ Schedule' }}
      </button>
    </div>

    <!-- Inline schedule editor -->
    <div v-if="showSchedule" class="mt-2 p-3 bg-gray-800/50 rounded-lg border border-gray-700 space-y-2">
      <div class="flex items-center gap-2">
        <select v-model="schedType" class="bg-gray-800 border border-gray-700 rounded px-2 py-1 text-xs text-gray-300">
          <option value="interval">Every N minutes</option>
          <option value="cron">Cron expression</option>
        </select>
        <input
          v-if="schedType === 'interval'"
          v-model.number="schedInterval"
          type="number"
          min="1"
          class="w-20 bg-gray-800 border border-gray-700 rounded px-2 py-1 text-xs text-gray-300"
          placeholder="15"
        />
        <input
          v-else
          v-model="schedCron"
          class="flex-1 bg-gray-800 border border-gray-700 rounded px-2 py-1 text-xs text-gray-300 font-mono"
          placeholder="*/15 * * * *"
        />
      </div>
      <div class="flex gap-2">
        <button @click="saveSchedule" class="px-3 py-1 bg-blue-600 text-white rounded text-xs">Save</button>
        <button v-if="schedule" @click="deleteSchedule" class="px-3 py-1 bg-red-600/20 text-red-400 rounded text-xs">Remove</button>
        <button @click="showSchedule = false" class="px-3 py-1 bg-gray-700 text-gray-300 rounded text-xs">Cancel</button>
      </div>
    </div>

    <!-- Progress bar when running -->
    <div v-if="progressData" class="mt-3">
      <div class="w-full h-1.5 bg-gray-800 rounded-full overflow-hidden">
        <div
          class="h-full bg-blue-500 transition-all duration-500"
          :style="{ width: `${progressData.data?.percentage || 0}%` }"
        />
      </div>
      <div class="flex justify-between mt-1 text-[10px] text-gray-500">
        <span>{{ progressData.data?.percentage || 0 }}%</span>
        <span>{{ formatSpeed(progressData.data?.speed || 0) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { PlayIcon, PauseIcon, TrashIcon, ArrowRightIcon, PencilSquareIcon } from '@heroicons/vue/24/outline'

const props = defineProps<{
  task: any
  progressData?: any
}>()

defineEmits<{
  (e: 'edit', task: any): void
  (e: 'run', id: number): void
  (e: 'toggle', id: number): void
  (e: 'delete', id: number): void
}>()

const modeLabels: Record<string, string> = {
  copy_to_local: 'Copy: Cloud -> Local',
  copy_to_remote: 'Copy: Local -> Cloud',
  sync_to_local: 'Sync: Cloud -> Local',
  sync_to_remote: 'Sync: Local -> Cloud',
  bisync: 'Bidirectional Sync',
}

const modeLabel = computed(() => modeLabels[props.task.sync_mode] || props.task.sync_mode)

// Schedule
const api = useApi()
const schedule = ref<any>(null)
const showSchedule = ref(false)
const schedType = ref('interval')
const schedInterval = ref(15)
const schedCron = ref('*/15 * * * *')

const scheduleLabel = computed(() => {
  if (!schedule.value) return ''
  if (schedule.value.schedule_type === 'interval') {
    const mins = Math.round((schedule.value.interval_seconds || 900) / 60)
    return `Every ${mins}m`
  }
  return schedule.value.cron_expression || 'cron'
})

async function loadSchedule() {
  try {
    const data = await api.get<any>(`/api/tasks/${props.task.id}/schedule`)
    schedule.value = data
    if (data) {
      schedType.value = data.schedule_type || 'interval'
      schedInterval.value = Math.round((data.interval_seconds || 900) / 60)
      schedCron.value = data.cron_expression || '*/15 * * * *'
    }
  } catch {
    schedule.value = null
  }
}

async function saveSchedule() {
  try {
    const body: any = {
      schedule_type: schedType.value,
      is_active: true,
    }
    if (schedType.value === 'interval') {
      body.interval_seconds = schedInterval.value * 60
    } else {
      body.cron_expression = schedCron.value
    }
    schedule.value = await api.put(`/api/tasks/${props.task.id}/schedule`, body)
    showSchedule.value = false
  } catch (e) {
    console.error(e)
  }
}

async function deleteSchedule() {
  try {
    await api.del(`/api/tasks/${props.task.id}/schedule`)
    schedule.value = null
    showSchedule.value = false
  } catch (e) {
    console.error(e)
  }
}

onMounted(loadSchedule)

function formatSpeed(bytesPerSec: number): string {
  if (bytesPerSec === 0) return ''
  const units = ['B/s', 'KB/s', 'MB/s', 'GB/s']
  const i = Math.floor(Math.log(bytesPerSec) / Math.log(1024))
  return `${(bytesPerSec / Math.pow(1024, i)).toFixed(1)} ${units[i]}`
}
</script>
