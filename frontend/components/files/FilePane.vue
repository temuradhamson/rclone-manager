<template>
  <div
    class="bg-gray-900 rounded-lg border border-gray-800 flex flex-col overflow-hidden"
    :class="{ 'border-blue-500/50': dragOver }"
    @dragover.prevent="onDragOver"
    @dragleave="dragOver = false"
    @drop.prevent="onDrop"
  >
    <!-- Header -->
    <div class="flex items-center gap-2 px-3 py-2 border-b border-gray-800 bg-gray-900/80">
      <span class="text-xs font-medium" :class="mode === 'remote' ? 'text-blue-400' : 'text-green-400'">
        {{ title }}
      </span>
      <select
        v-model="currentStorage"
        class="bg-gray-800 border border-gray-700 rounded px-2 py-1 text-xs text-gray-300 outline-none"
        @change="navigateTo(currentStorage)"
      >
        <option v-for="s in storages" :key="s" :value="s">{{ s }}</option>
      </select>
      <div class="flex-1" />
      <!-- Actions -->
      <button
        @click="showNewFolder = true"
        class="text-gray-500 hover:text-white transition p-1"
        title="New Folder"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
      </button>
      <button
        @click="loadFiles()"
        class="text-gray-500 hover:text-white transition p-1"
        title="Refresh"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
      </button>
    </div>

    <!-- Breadcrumb -->
    <div class="flex items-center gap-1 px-3 py-1.5 border-b border-gray-800/50 text-xs overflow-x-auto">
      <button
        v-for="(crumb, i) in breadcrumbs"
        :key="i"
        @click="navigateTo(crumb.path)"
        class="text-gray-500 hover:text-blue-400 transition whitespace-nowrap flex items-center gap-1"
      >
        <span v-if="i > 0" class="text-gray-700">/</span>
        {{ crumb.label }}
      </button>
    </div>

    <!-- New folder input -->
    <div v-if="showNewFolder" class="flex gap-2 px-3 py-2 border-b border-gray-800/50">
      <input
        v-model="newFolderName"
        ref="newFolderInput"
        class="flex-1 bg-gray-800 border border-gray-700 rounded px-2 py-1 text-xs text-gray-300 outline-none focus:border-blue-500"
        placeholder="Folder name"
        @keydown.enter="createFolder"
        @keydown.escape="showNewFolder = false"
      />
      <button @click="createFolder" class="px-2 py-1 bg-blue-600 text-white rounded text-xs">Create</button>
      <button @click="showNewFolder = false" class="px-2 py-1 bg-gray-700 text-gray-300 rounded text-xs">Cancel</button>
    </div>

    <!-- File list -->
    <div class="flex-1 overflow-y-auto" v-if="!loading">
      <!-- Go up -->
      <div
        v-if="canGoUp"
        @click="goUp"
        class="flex items-center gap-2 px-3 py-1.5 hover:bg-gray-800/50 cursor-pointer text-gray-500 border-b border-gray-800/30"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h10a5 5 0 015 5v4M3 10l6 6M3 10l6-6" />
        </svg>
        <span class="text-xs">..</span>
      </div>

      <!-- Files -->
      <div
        v-for="file in files"
        :key="file.path"
        class="flex items-center gap-2 px-3 py-1.5 hover:bg-gray-800/50 cursor-pointer group transition-colors"
        :class="{ 'bg-blue-900/20': selectedFile?.path === file.path }"
        :draggable="file.type === 'dir'"
        @dragstart="onDragStart($event, file)"
        @click="onFileClick(file)"
        @dblclick="onFileDblClick(file)"
        @contextmenu.prevent="openContextMenu($event, file)"
      >
        <!-- Icon -->
        <span class="w-4 h-4 flex-shrink-0" :class="file.type === 'dir' ? 'text-yellow-400' : 'text-gray-500'">
          <svg v-if="file.type === 'dir'" fill="currentColor" viewBox="0 0 20 20">
            <path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" />
          </svg>
          <svg v-else fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
          </svg>
        </span>

        <span class="flex-1 text-xs text-gray-300 truncate">{{ file.basename }}</span>

        <span v-if="file.type !== 'dir' && file.size" class="text-[10px] text-gray-600 flex-shrink-0">
          {{ formatSize(file.size) }}
        </span>

        <!-- Delete button (hover) -->
        <button
          @click.stop="deleteItem(file)"
          class="opacity-0 group-hover:opacity-100 text-gray-600 hover:text-red-400 transition p-0.5"
          title="Delete"
        >
          <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div v-if="files.length === 0" class="flex items-center justify-center h-32 text-gray-600 text-xs">
        Empty folder
      </div>
    </div>

    <!-- Loading -->
    <div v-else class="flex-1 flex items-center justify-center text-gray-600 text-xs">
      Loading...
    </div>

    <!-- Context menu -->
    <Teleport to="body">
      <div
        v-if="contextMenu.show"
        class="fixed bg-gray-800 border border-gray-700 rounded-lg shadow-xl py-1 z-50 min-w-[150px]"
        :style="{ left: contextMenu.x + 'px', top: contextMenu.y + 'px' }"
        @click="contextMenu.show = false"
      >
        <button @click="startRename" class="w-full text-left px-3 py-1.5 text-xs text-gray-300 hover:bg-gray-700">Rename</button>
        <button @click="deleteItem(contextMenu.file)" class="w-full text-left px-3 py-1.5 text-xs text-red-400 hover:bg-gray-700">Delete</button>
      </div>
    </Teleport>

    <!-- Rename dialog -->
    <Teleport to="body">
      <div v-if="renaming" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="renaming = false">
        <div class="bg-gray-900 border border-gray-700 rounded-lg p-4 w-80">
          <p class="text-sm text-gray-300 mb-2">Rename</p>
          <input
            v-model="renameValue"
            class="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-gray-300 outline-none focus:border-blue-500"
            @keydown.enter="doRename"
          />
          <div class="flex justify-end gap-2 mt-3">
            <button @click="renaming = false" class="px-3 py-1.5 bg-gray-700 text-gray-300 rounded text-xs">Cancel</button>
            <button @click="doRename" class="px-3 py-1.5 bg-blue-600 text-white rounded text-xs">Rename</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  title: string
  storages: string[]
  initialStorage: string
  mode: 'remote' | 'local'
}>()

const emit = defineEmits<{
  drop: [data: { src: any; dstPath: string }]
}>()

const api = useApi()

const currentStorage = ref(props.initialStorage)
const currentPath = ref('')
const files = ref<any[]>([])
const loading = ref(false)
const selectedFile = ref<any>(null)
const dragOver = ref(false)

// New folder
const showNewFolder = ref(false)
const newFolderName = ref('')
const newFolderInput = ref<HTMLInputElement>()

// Context menu
const contextMenu = reactive({ show: false, x: 0, y: 0, file: null as any })

// Rename
const renaming = ref(false)
const renameValue = ref('')
const renameFile = ref<any>(null)

const canGoUp = computed(() => {
  return currentPath.value && currentPath.value !== currentStorage.value
})

const breadcrumbs = computed(() => {
  const parts = currentPath.value.replace(/\\/g, '/').split('/').filter(Boolean)
  const crumbs: { label: string; path: string }[] = []
  let acc = ''
  for (const p of parts) {
    acc += (acc ? '/' : '') + p
    crumbs.push({ label: p, path: acc })
  }
  return crumbs
})

function formatSize(bytes: number): string {
  if (!bytes || bytes <= 0) return ''
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`
}

async function loadFiles(path?: string) {
  const target = path || currentPath.value || currentStorage.value
  loading.value = true
  try {
    const data = await api.post<any>('/api/fm/list', { path: target })
    files.value = data.files || []
    currentPath.value = target
  } catch (e) {
    console.error(e)
    files.value = []
  } finally {
    loading.value = false
  }
}

function navigateTo(path: string) {
  currentPath.value = path
  loadFiles(path)
}

function goUp() {
  const parts = currentPath.value.replace(/\\/g, '/').replace(/\/$/, '').split('/')
  parts.pop()
  const parent = parts.join('/') || currentStorage.value
  navigateTo(parent)
}

function onFileClick(file: any) {
  selectedFile.value = file
}

function onFileDblClick(file: any) {
  if (file.type === 'dir') {
    navigateTo(file.path)
  } else {
    // Preview: open in new tab
    const ext = file.basename.split('.').pop()?.toLowerCase() || ''
    const mediaExts = ['mp4','mkv','webm','mov','mp3','wav','flac','ogg','m4a','jpg','jpeg','png','gif','webp','bmp','pdf','txt','json','csv','md','html','css','js']
    if (mediaExts.includes(ext)) {
      const url = `http://127.0.0.1:8001/api/fm/preview?path=${encodeURIComponent(file.path)}`
      window.open(url, '_blank')
    }
  }
}

// Drag & Drop
function onDragStart(e: DragEvent, file: any) {
  e.dataTransfer?.setData('application/json', JSON.stringify({
    name: file.basename,
    fullPath: file.path,
    mode: props.mode,
    type: file.type,
  }))
}

function onDragOver(e: DragEvent) {
  dragOver.value = true
}

function onDrop(e: DragEvent) {
  dragOver.value = false
  const raw = e.dataTransfer?.getData('application/json')
  if (!raw) return
  try {
    const src = JSON.parse(raw)
    if (src.mode === props.mode) return // same pane, ignore
    emit('drop', { src, dstPath: currentPath.value || currentStorage.value })
  } catch {}
}

// Create folder
async function createFolder() {
  if (!newFolderName.value.trim()) return
  try {
    await api.post('/api/fm/createFolder', { path: currentPath.value, name: newFolderName.value.trim() })
    newFolderName.value = ''
    showNewFolder.value = false
    loadFiles()
  } catch (e) {
    console.error(e)
  }
}

// Delete
async function deleteItem(file: any) {
  if (!confirm(`Delete "${file.basename}"?`)) return
  try {
    await api.post('/api/fm/delete', {
      path: currentPath.value,
      items: [{ path: file.path, type: file.type }],
    })
    loadFiles()
  } catch (e) {
    console.error(e)
  }
}

// Context menu
function openContextMenu(e: MouseEvent, file: any) {
  contextMenu.show = true
  contextMenu.x = e.clientX
  contextMenu.y = e.clientY
  contextMenu.file = file
}

// Rename
function startRename() {
  renameFile.value = contextMenu.file
  renameValue.value = contextMenu.file.basename
  renaming.value = true
}

async function doRename() {
  if (!renameValue.value.trim() || !renameFile.value) return
  try {
    await api.post('/api/fm/rename', {
      path: currentPath.value,
      item: renameFile.value.path,
      name: renameValue.value.trim(),
    })
    renaming.value = false
    loadFiles()
  } catch (e) {
    console.error(e)
  }
}

// Close context menu on click outside
onMounted(() => {
  document.addEventListener('click', () => { contextMenu.show = false })
  loadFiles()
})

watch(() => props.initialStorage, (v) => {
  if (v) {
    currentStorage.value = v
    loadFiles(v)
  }
})
</script>
