<template>
  <Teleport to="body">
    <div
      v-if="show"
      class="fixed inset-0 z-50 flex items-center justify-center"
      @click.self="$emit('close')"
    >
      <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" />

      <div class="relative bg-gray-900 border border-gray-700 rounded-xl shadow-2xl w-[560px] max-h-[90vh] overflow-y-auto">
        <!-- Header -->
        <div class="p-5 border-b border-gray-800">
          <h2 class="text-lg font-semibold text-white">
            {{ isEdit ? 'Edit Sync Task' : 'Create Sync Task' }}
          </h2>
          <p class="text-xs text-gray-500 mt-1">
            {{ isEdit ? 'Modify sync behavior and rules' : 'Configure how these folders should be linked' }}
          </p>
        </div>

        <!-- Paths preview -->
        <div class="px-5 py-4 bg-gray-950/50 border-b border-gray-800">
          <div class="flex items-center gap-3">
            <div class="flex-1 min-w-0">
              <p class="text-[10px] text-gray-500 uppercase tracking-wider mb-1">Source</p>
              <input
                v-model="form.src_path"
                class="w-full bg-gray-900 rounded-lg px-3 py-2 text-sm text-white border border-gray-800 focus:border-blue-500 outline-none"
                :readonly="!isEdit"
              />
            </div>
            <ArrowRightIcon class="w-5 h-5 text-gray-600 shrink-0 mt-5" />
            <div class="flex-1 min-w-0">
              <p class="text-[10px] text-gray-500 uppercase tracking-wider mb-1">Destination</p>
              <input
                v-model="form.dst_path"
                class="w-full bg-gray-900 rounded-lg px-3 py-2 text-sm text-white border border-gray-800 focus:border-blue-500 outline-none"
                :readonly="!isEdit"
              />
            </div>
          </div>
        </div>

        <form @submit.prevent="submit" class="p-5 space-y-5">
          <!-- Task name -->
          <div>
            <label class="block text-xs text-gray-400 mb-1.5">Task Name</label>
            <input
              v-model="form.name"
              required
              class="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:border-blue-500 outline-none"
            />
          </div>

          <!-- Description -->
          <div>
            <label class="block text-xs text-gray-400 mb-1.5">Description</label>
            <input
              v-model="form.description"
              class="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:border-blue-500 outline-none"
              placeholder="Optional notes"
            />
          </div>

          <!-- Sync mode -->
          <div>
            <label class="block text-xs text-gray-400 mb-2">Sync Mode</label>
            <div class="grid grid-cols-2 gap-2">
              <label
                v-for="mode in allModes"
                :key="mode.value"
                class="flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-all"
                :class="form.sync_mode === mode.value
                  ? 'border-blue-500 bg-blue-950/30'
                  : 'border-gray-700 hover:border-gray-600'"
              >
                <input type="radio" v-model="form.sync_mode" :value="mode.value" class="hidden" />
                <span class="text-xl leading-none mt-0.5">{{ mode.icon }}</span>
                <div>
                  <p class="text-sm text-white font-medium">{{ mode.label }}</p>
                  <p class="text-[11px] text-gray-500 mt-0.5">{{ mode.desc }}</p>
                </div>
              </label>
            </div>
          </div>

          <!-- On delete rule -->
          <div>
            <label class="block text-xs text-gray-400 mb-1.5">When files are deleted</label>
            <div
              v-if="isCopyMode"
              class="px-3 py-2 bg-gray-800/50 border border-gray-700 rounded-lg text-xs text-gray-500"
            >
              Copy mode only adds new files — it never deletes. Switch to Mirror or Bidirectional to manage deletions.
            </div>
            <select
              v-else
              v-model="form.onDelete"
              class="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white outline-none"
            >
              <option value="delete_immediate">Delete immediately</option>
              <option value="backup">Keep backup for N days</option>
              <option value="move_to_trash">Move to trash folder</option>
              <option value="skip">Don't delete</option>
            </select>
          </div>

          <div v-if="form.onDelete === 'backup'" class="flex gap-3">
            <div class="flex-1">
              <label class="block text-xs text-gray-400 mb-1.5">Keep backups for (days)</label>
              <input
                v-model.number="form.retentionDays"
                type="number"
                min="1"
                class="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white outline-none"
              />
            </div>
            <div class="flex-1">
              <label class="block text-xs text-gray-400 mb-1.5">Backup folder</label>
              <input
                v-model="form.backupDir"
                class="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white outline-none"
                placeholder="e.g. E:/backups"
              />
            </div>
          </div>

          <div v-if="form.onDelete === 'move_to_trash'">
            <label class="block text-xs text-gray-400 mb-1.5">Trash folder</label>
            <input
              v-model="form.trashDir"
              class="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white outline-none"
              placeholder="e.g. E:/.trash"
            />
          </div>

          <!-- Enabled toggle (edit only) -->
          <div v-if="isEdit" class="flex items-center justify-between py-2 border-t border-gray-800">
            <span class="text-sm text-gray-300">Task enabled</span>
            <button
              type="button"
              class="w-10 h-5 rounded-full transition-colors relative"
              :class="form.is_enabled ? 'bg-blue-600' : 'bg-gray-700'"
              @click="form.is_enabled = !form.is_enabled"
            >
              <span
                class="absolute top-0.5 w-4 h-4 bg-white rounded-full transition-transform"
                :class="form.is_enabled ? 'translate-x-5' : 'translate-x-0.5'"
              />
            </button>
          </div>

          <!-- Actions -->
          <div class="flex gap-3 pt-2">
            <button
              type="submit"
              :disabled="submitting"
              class="flex-1 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors"
            >
              {{ submitting ? 'Saving...' : (isEdit ? 'Save Changes' : 'Create Task') }}
            </button>
            <button
              type="button"
              class="px-5 py-2.5 bg-gray-800 hover:bg-gray-700 text-gray-300 text-sm rounded-lg transition-colors"
              @click="$emit('close')"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ArrowRightIcon } from '@heroicons/vue/24/outline'

const props = defineProps<{
  show: boolean
  // Create mode props
  srcPath?: string
  srcMode?: 'remote' | 'local'
  srcName?: string
  dstPath?: string
  dstMode?: 'remote' | 'local'
  // Edit mode props
  task?: any
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'saved', task: any): void
}>()

const store = useTasksStore()
const api = useApi()
const submitting = ref(false)

const isEdit = computed(() => !!props.task)

const form = reactive({
  name: '',
  description: '',
  src_type: 'remote',
  src_path: '',
  dst_type: 'local',
  dst_path: '',
  sync_mode: 'copy_to_local',
  is_enabled: true,
  onDelete: 'delete_immediate',
  retentionDays: 30,
  backupDir: '',
  trashDir: '',
})

const isCopyMode = computed(() => form.sync_mode.startsWith('copy_'))

const allModes = [
  { value: 'copy_to_local', label: 'Copy to Local', icon: '↓', desc: 'Download cloud files, keep both independent' },
  { value: 'copy_to_remote', label: 'Copy to Cloud', icon: '↑', desc: 'Upload local files, keep both independent' },
  { value: 'sync_to_local', label: 'Mirror to Local', icon: '⇊', desc: 'Local becomes exact copy of cloud' },
  { value: 'sync_to_remote', label: 'Mirror to Cloud', icon: '⇈', desc: 'Cloud becomes exact copy of local' },
  { value: 'bisync', label: 'Bidirectional', icon: '⇅', desc: 'Changes sync both ways' },
]

watch(() => props.show, async (val) => {
  if (!val) return

  if (props.task) {
    // Edit mode — fill from existing task
    form.name = props.task.name || ''
    form.description = props.task.description || ''
    form.src_type = props.task.src_type
    form.src_path = props.task.src_path
    form.dst_type = props.task.dst_type
    form.dst_path = props.task.dst_path
    form.sync_mode = props.task.sync_mode
    form.is_enabled = props.task.is_enabled

    // Load existing rules
    try {
      const rules = await api.get<any[]>(`/api/tasks/${props.task.id}/rules`)
      const deleteRule = rules.find((r: any) => r.rule_type === 'on_delete')
      if (deleteRule) {
        form.onDelete = deleteRule.action
        form.retentionDays = deleteRule.retention_days || 30
        form.backupDir = deleteRule.backup_dir || ''
        form.trashDir = deleteRule.trash_dir || ''
      } else {
        form.onDelete = 'delete_immediate'
      }
    } catch {
      form.onDelete = 'delete_immediate'
    }
  } else {
    // Create mode
    form.name = `Sync ${props.srcName || ''}`
    form.description = ''
    form.src_type = props.srcMode || 'remote'
    form.src_path = props.srcPath || ''
    form.dst_type = props.dstMode || 'local'
    form.dst_path = props.dstPath || ''
    form.sync_mode = props.srcMode === 'remote' ? 'copy_to_local' : 'copy_to_remote'
    form.is_enabled = true
    form.onDelete = 'delete_immediate'
    form.retentionDays = 30
    form.backupDir = ''
    form.trashDir = ''
  }
})

async function submit() {
  submitting.value = true
  try {
    let task: any

    if (isEdit.value) {
      // Update task
      task = await store.updateTask(props.task.id, {
        name: form.name,
        description: form.description || null,
        src_type: form.src_type,
        src_path: form.src_path,
        dst_type: form.dst_type,
        dst_path: form.dst_path,
        sync_mode: form.sync_mode,
        is_enabled: form.is_enabled,
      })

      // Update rules: delete old on_delete rules, create new one
      const existingRules = await api.get<any[]>(`/api/tasks/${props.task.id}/rules`)
      for (const rule of existingRules.filter((r: any) => r.rule_type === 'on_delete')) {
        await api.del(`/api/tasks/rules/${rule.id}`)
      }
    } else {
      // Create task
      task = await store.createTask({
        name: form.name,
        description: form.description || undefined,
        src_type: form.src_type,
        src_path: form.src_path,
        dst_type: form.dst_type,
        dst_path: form.dst_path,
        sync_mode: form.sync_mode,
      })
    }

    // Create rule if not default
    if (form.onDelete !== 'delete_immediate') {
      const ruleData: any = {
        rule_type: 'on_delete',
        action: form.onDelete,
        priority: 10,
      }
      if (form.onDelete === 'backup') {
        ruleData.backup_dir = form.backupDir || `${form.dst_path}/.backups`
        ruleData.retention_days = form.retentionDays
      }
      if (form.onDelete === 'move_to_trash') {
        ruleData.trash_dir = form.trashDir || `${form.dst_path}/.trash`
      }
      await api.post(`/api/tasks/${task.id}/rules`, ruleData)
    }

    emit('saved', task)
    emit('close')
  } finally {
    submitting.value = false
  }
}
</script>
