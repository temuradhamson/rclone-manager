<template>
  <div
    class="bg-gray-900 rounded-lg border h-full flex flex-col transition-colors"
    :class="dragOver ? 'border-blue-500 bg-blue-950/20' : 'border-gray-800'"
    @dragover.prevent="onDragOver"
    @dragleave="onDragLeave"
    @drop.prevent="onDrop"
  >
    <div class="p-3 border-b border-gray-800 flex items-center justify-between">
      <h3 class="text-sm font-medium text-gray-300">{{ title }}</h3>
      <button
        v-if="currentPath"
        class="text-xs text-gray-500 hover:text-white"
        @click="goUp"
      >
        .. up
      </button>
    </div>

    <!-- Breadcrumb -->
    <div v-if="currentPath" class="px-3 py-1.5 text-xs text-gray-500 border-b border-gray-800 truncate">
      {{ fullCurrentPath }}
    </div>

    <!-- Drop hint -->
    <div v-if="dragOver" class="px-3 py-2 text-xs text-blue-400 bg-blue-950/30 border-b border-blue-900/50">
      Drop here to create sync task
    </div>

    <!-- File list -->
    <div class="flex-1 overflow-y-auto p-1">
      <div v-if="loading" class="p-4 text-center text-gray-500 text-sm">Loading...</div>
      <div
        v-for="item in items"
        :key="item.path"
        class="flex items-center gap-2 px-3 py-1.5 rounded cursor-pointer text-sm hover:bg-gray-800 transition-colors"
        :class="selectedPath === item.path ? 'bg-gray-800 text-blue-400' : 'text-gray-300'"
        :draggable="item.is_dir"
        @dragstart="onDragStart($event, item)"
        @click="onItemClick(item)"
        @dblclick="onItemDblClick(item)"
      >
        <FolderIcon v-if="item.is_dir" class="w-4 h-4 text-yellow-500 shrink-0" />
        <DocumentIcon v-else class="w-4 h-4 text-gray-500 shrink-0" />
        <span class="truncate">{{ item.name }}</span>
        <span v-if="item.is_dir" class="ml-auto opacity-0 group-hover:opacity-100">
          <ArrowsRightLeftIcon class="w-3 h-3 text-gray-600" />
        </span>
        <span v-else-if="item.size && item.size > 0" class="ml-auto text-xs text-gray-600 shrink-0">
          {{ formatSize(item.size) }}
        </span>
      </div>
      <div v-if="!loading && items.length === 0" class="p-4 text-center text-gray-600 text-sm">
        Empty folder
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { FolderIcon, DocumentIcon } from '@heroicons/vue/24/solid'
import { ArrowsRightLeftIcon } from '@heroicons/vue/24/outline'

interface FileItem {
  name: string
  path: string
  size: number
  is_dir: boolean
  mod_time?: string | number
  total_bytes?: number
  free_bytes?: number
}

const props = defineProps<{
  title: string
  mode: 'remote' | 'local'
  fs?: string
}>()

const emit = defineEmits<{
  (e: 'select', path: string): void
  (e: 'drop', data: { src: DragPayload, dstPath: string, dstMode: string }): void
}>()

export interface DragPayload {
  name: string
  path: string
  fullPath: string
  mode: 'remote' | 'local'
}

const api = useApi()
const items = ref<FileItem[]>([])
const currentPath = ref('')
const selectedPath = ref('')
const loading = ref(false)
const dragOver = ref(false)

const fullCurrentPath = computed(() => {
  if (props.mode === 'remote' && props.fs) {
    return `${props.fs}${currentPath.value}`
  }
  return currentPath.value
})

async function loadItems(path: string = '') {
  loading.value = true
  try {
    if (props.mode === 'remote' && props.fs) {
      items.value = await api.get<FileItem[]>('/api/files/list', { fs: props.fs, path })
    } else if (props.mode === 'local') {
      if (!path) {
        items.value = await api.get<FileItem[]>('/api/files/local/drives')
      } else {
        items.value = await api.get<FileItem[]>('/api/files/local', { path })
      }
    }
    currentPath.value = path
  } catch (err) {
    console.error('Failed to load files:', err)
  } finally {
    loading.value = false
  }
}

function onDragStart(event: DragEvent, item: FileItem) {
  if (!event.dataTransfer || !item.is_dir) return
  const fullPath = props.mode === 'remote' && props.fs
    ? `${props.fs}${item.path}`
    : item.path
  const payload: DragPayload = {
    name: item.name,
    path: item.path,
    fullPath,
    mode: props.mode,
  }
  event.dataTransfer.setData('application/json', JSON.stringify(payload))
  event.dataTransfer.effectAllowed = 'link'
}

function onDragOver(event: DragEvent) {
  dragOver.value = true
  if (event.dataTransfer) event.dataTransfer.dropEffect = 'link'
}

function onDragLeave() {
  dragOver.value = false
}

function onDrop(event: DragEvent) {
  dragOver.value = false
  if (!event.dataTransfer) return
  const raw = event.dataTransfer.getData('application/json')
  if (!raw) return
  try {
    const src: DragPayload = JSON.parse(raw)
    // Don't drop onto the same panel type
    if (src.mode === props.mode) return
    const dstPath = fullCurrentPath.value || (props.mode === 'local' ? '' : '')
    emit('drop', { src, dstPath, dstMode: props.mode })
  } catch {}
}

function onItemClick(item: FileItem) {
  selectedPath.value = item.path
  const fullPath = props.mode === 'remote' && props.fs
    ? `${props.fs}${item.path}`
    : item.path
  emit('select', fullPath)
}

function onItemDblClick(item: FileItem) {
  if (item.is_dir) {
    loadItems(item.path)
  }
}

function goUp() {
  if (!currentPath.value) return
  const parts = currentPath.value.replace(/\\/g, '/').split('/').filter(Boolean)
  parts.pop()
  loadItems(parts.join('/'))
}

function formatSize(bytes: number): string {
  if (bytes <= 0) return ''
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return `${(bytes / Math.pow(1024, i)).toFixed(i > 0 ? 1 : 0)} ${units[i]}`
}

watch(() => props.fs, (newFs) => {
  if (newFs) {
    items.value = []
    currentPath.value = ''
    selectedPath.value = ''
    loadItems()
  }
})

onMounted(() => {
  if (props.mode === 'local' || props.fs) {
    loadItems()
  }
})
</script>
