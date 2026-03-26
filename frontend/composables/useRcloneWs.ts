interface ProgressData {
  type: string
  task_id: number
  execution_id: number
  data?: {
    bytes: number
    totalBytes: number
    speed: number
    eta: number
    percentage: number
    transfers: number
    transferring: any[]
  }
  error?: string
}

export function useRcloneWs() {
  const config = useRuntimeConfig()
  const progress = ref<Map<number, ProgressData>>(new Map())
  const events = ref<ProgressData[]>([])
  let ws: WebSocket | null = null

  function connect() {
    ws = new WebSocket(`${config.public.wsBase}/api/ws/progress`)

    ws.onmessage = (event) => {
      const msg: ProgressData = JSON.parse(event.data)
      if (msg.type === 'progress') {
        progress.value.set(msg.task_id, msg)
      } else {
        events.value.unshift(msg)
        if (events.value.length > 50) events.value.pop()
        if (msg.type === 'task_completed' || msg.type === 'task_failed') {
          progress.value.delete(msg.task_id)
        }
      }
    }

    ws.onclose = () => {
      setTimeout(connect, 3000)
    }
  }

  function disconnect() {
    ws?.close()
    ws = null
  }

  return { progress, events, connect, disconnect }
}
