<template>
  <div class="space-y-3">
    <div class="flex items-center justify-between">
      <h2 class="text-lg font-semibold text-white">File Browser</h2>
      <p class="text-xs text-gray-600">Drag a folder from cloud to local (or vice versa) to create a sync task</p>
    </div>

    <div class="grid grid-cols-2 gap-3 h-[calc(100vh-170px)]">
      <!-- LEFT: Remote (Cloud) -->
      <FilesFilePane
        title="Cloud"
        :storages="remoteStorages"
        :initial-storage="remoteStorages[0] || ''"
        mode="remote"
        @drop="onDropToRemote"
      />

      <!-- RIGHT: Local -->
      <FilesFilePane
        title="Local"
        :storages="localStorages"
        :initial-storage="localStorages[0] || ''"
        mode="local"
        @drop="onDropToLocal"
      />
    </div>

    <!-- Create task modal -->
    <TasksTaskModal
      v-if="showModal"
      :show="showModal"
      :src-path="modalSrc.path"
      :src-mode="modalSrc.mode"
      :src-name="modalSrc.name"
      :dst-path="modalDst.path"
      :dst-mode="modalDst.mode"
      @close="showModal = false"
      @saved="onTaskCreated"
    />
  </div>
</template>

<script setup lang="ts">
const api = useApi()

const remoteStorages = ref<string[]>([])
const localStorages = ['C:/', 'D:/', 'E:/', 'F:/', 'G:/']

const showModal = ref(false)
const modalSrc = ref({ name: '', path: '', mode: 'remote' as string })
const modalDst = ref({ path: '', mode: 'local' as string })

function onDropToLocal(data: { src: any; dstPath: string }) {
  modalSrc.value = { name: data.src.name, path: data.src.fullPath, mode: 'remote' }
  modalDst.value = { path: `${data.dstPath}/${data.src.name}`, mode: 'local' }
  showModal.value = true
}

function onDropToRemote(data: { src: any; dstPath: string }) {
  modalSrc.value = { name: data.src.name, path: data.src.fullPath, mode: 'local' }
  modalDst.value = { path: `${data.dstPath}/${data.src.name}`, mode: 'remote' }
  showModal.value = true
}

function onTaskCreated() {
  showModal.value = false
}

onMounted(async () => {
  try {
    const data = await api.get<{ name: string }[]>('/api/remotes')
    remoteStorages.value = data.map(r => r.name + ':')
  } catch {}
})
</script>
