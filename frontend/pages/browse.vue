<template>
  <div class="space-y-4">
    <!-- Top bar -->
    <div class="flex items-center gap-4 bg-gray-900 rounded-lg border border-gray-800 p-3">
      <label class="text-sm text-gray-400">Remote:</label>
      <select
        v-model="selectedRemote"
        class="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-white focus:border-blue-500 outline-none"
      >
        <option v-for="r in remotes" :key="r" :value="r">{{ r }}</option>
      </select>
      <div class="flex-1" />
      <p class="text-xs text-gray-600">Drag a folder from one panel to the other to create a sync task</p>
    </div>

    <!-- Dual pane file browser -->
    <div class="grid grid-cols-2 gap-4 h-[calc(100vh-200px)]">
      <FilesFileTree
        v-if="selectedRemote"
        :key="'remote-' + selectedRemote"
        title="Cloud"
        mode="remote"
        :fs="selectedRemote + ':'"
        @select="selectedSrc = $event"
        @drop="onDropToRemote"
      />
      <div v-else class="bg-gray-900 rounded-lg border border-gray-800 flex items-center justify-center text-gray-600 text-sm">
        Select a remote to browse
      </div>

      <FilesFileTree
        title="Local Drives"
        mode="local"
        @select="selectedDst = $event"
        @drop="onDropToLocal"
      />
    </div>

    <!-- Create task modal -->
    <TasksTaskModal
      :show="showModal"
      :src-path="modalSrc.fullPath"
      :src-mode="modalSrc.mode"
      :src-name="modalSrc.name"
      :dst-path="modalDst"
      :dst-mode="modalDstMode"
      @close="showModal = false"
      @saved="onTaskCreated"
    />
  </div>
</template>

<script setup lang="ts">
const api = useApi()
const store = useTasksStore()

const remotes = ref<string[]>([])
const selectedRemote = ref('')
const selectedSrc = ref('')
const selectedDst = ref('')

// Modal state
const showModal = ref(false)
const modalSrc = ref({ name: '', fullPath: '', mode: 'remote' as 'remote' | 'local' })
const modalDst = ref('')
const modalDstMode = ref<'remote' | 'local'>('local')

function onDropToLocal(data: { src: any, dstPath: string, dstMode: string }) {
  // Dragged from cloud to local panel
  const destPath = data.dstPath || selectedDst.value
  if (!destPath) return

  // Auto-append source folder name to destination
  const dstFull = destPath.endsWith('/') || destPath.endsWith('\\')
    ? `${destPath}${data.src.name}`
    : `${destPath}/${data.src.name}`

  modalSrc.value = { name: data.src.name, fullPath: data.src.fullPath, mode: data.src.mode }
  modalDst.value = dstFull
  modalDstMode.value = 'local'
  showModal.value = true
}

function onDropToRemote(data: { src: any, dstPath: string, dstMode: string }) {
  // Dragged from local to cloud panel
  const destPath = data.dstPath || selectedSrc.value
  if (!destPath) return

  const dstFull = `${destPath}/${data.src.name}`

  modalSrc.value = { name: data.src.name, fullPath: data.src.fullPath, mode: data.src.mode }
  modalDst.value = dstFull
  modalDstMode.value = 'remote'
  showModal.value = true
}

function onTaskCreated(task: any) {
  showModal.value = false
}

onMounted(async () => {
  try {
    const data = await api.get<{ name: string }[]>('/api/remotes')
    remotes.value = data.map(r => r.name)
    if (remotes.value.length > 0) {
      selectedRemote.value = remotes.value[0]
    }
  } catch {}
})
</script>
