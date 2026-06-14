<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <p class="text-sm text-gray-500">{{ store.tasks.length }} tasks configured</p>
    </div>

    <div v-if="store.loading" class="text-center text-gray-500 py-10">Loading...</div>

    <div v-else class="grid grid-cols-2 gap-3">
      <TasksTaskCard
        v-for="task in store.tasks"
        :key="task.id"
        :task="task"
        :progress-data="wsProgress.get(task.id)"
        @edit="openEdit"
        @run="store.runTask"
        @toggle="store.toggleTask"
        @delete="handleDelete"
      />
    </div>

    <div v-if="!store.loading && store.tasks.length === 0" class="text-center py-20">
      <p class="text-gray-500">No sync tasks yet</p>
      <NuxtLink to="/browse" class="text-blue-400 text-sm hover:text-blue-300 mt-2 inline-block">
        Go to File Browser to create one
      </NuxtLink>
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
const store = useTasksStore()
const { progress: wsProgress, connect } = useRcloneWs()

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

async function handleDelete(id: number) {
  if (confirm('Delete this task?')) {
    await store.deleteTask(id)
  }
}

onMounted(() => {
  connect()
  store.fetchTasks()
})
</script>
