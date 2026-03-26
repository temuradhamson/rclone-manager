import { defineStore } from 'pinia'

interface SyncTask {
  id: number
  name: string
  description: string | null
  src_type: string
  src_path: string
  dst_type: string
  dst_path: string
  sync_mode: string
  is_enabled: boolean
  extra_flags: string | null
  created_at: string
  updated_at: string
}

export const useTasksStore = defineStore('tasks', () => {
  const tasks = ref<SyncTask[]>([])
  const loading = ref(false)
  const api = useApi()

  async function fetchTasks() {
    loading.value = true
    try {
      tasks.value = await api.get<SyncTask[]>('/api/tasks')
    } finally {
      loading.value = false
    }
  }

  async function createTask(data: Partial<SyncTask>) {
    const task = await api.post<SyncTask>('/api/tasks', data)
    tasks.value.unshift(task)
    return task
  }

  async function deleteTask(id: number) {
    await api.del(`/api/tasks/${id}`)
    tasks.value = tasks.value.filter(t => t.id !== id)
  }

  async function toggleTask(id: number) {
    const task = await api.patch<SyncTask>(`/api/tasks/${id}/toggle`)
    const idx = tasks.value.findIndex(t => t.id === id)
    if (idx !== -1) tasks.value[idx] = task
  }

  async function runTask(id: number) {
    return await api.post(`/api/tasks/${id}/run`)
  }

  async function updateTask(id: number, data: Partial<SyncTask>) {
    const task = await api.put<SyncTask>(`/api/tasks/${id}`, data)
    const idx = tasks.value.findIndex(t => t.id === id)
    if (idx !== -1) tasks.value[idx] = task
    return task
  }

  async function stopTask(id: number) {
    return await api.post(`/api/tasks/${id}/stop`)
  }

  return { tasks, loading, fetchTasks, createTask, updateTask, deleteTask, toggleTask, runTask, stopTask }
})
