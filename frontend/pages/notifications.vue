<template>
  <div class="space-y-6">
    <h2 class="text-lg font-semibold text-white">Notification Settings</h2>

    <div class="bg-gray-900 rounded-lg border border-gray-800 p-6 space-y-5 max-w-xl">
      <!-- Telegram Config -->
      <div>
        <h3 class="text-sm font-medium text-gray-300 mb-3">Telegram Bot</h3>
        <div class="space-y-3">
          <div>
            <label class="text-xs text-gray-500 block mb-1">Bot Token</label>
            <input
              v-model="settings.telegram_bot_token"
              type="password"
              class="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300"
              placeholder="123456:ABC-DEF1234..."
            />
          </div>
          <div>
            <label class="text-xs text-gray-500 block mb-1">Chat ID</label>
            <input
              v-model="settings.telegram_chat_id"
              class="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300"
              placeholder="-1001234567890"
            />
          </div>
        </div>
      </div>

      <!-- Notification types -->
      <div>
        <h3 class="text-sm font-medium text-gray-300 mb-3">Notify When</h3>
        <div class="space-y-2">
          <label class="flex items-center gap-3 cursor-pointer">
            <input type="checkbox" v-model="settings.notify_on_error" class="accent-red-500 w-4 h-4" />
            <span class="text-sm text-gray-400">Sync errors</span>
            <span class="text-xs text-red-400/60 ml-auto">recommended</span>
          </label>
          <label class="flex items-center gap-3 cursor-pointer">
            <input type="checkbox" v-model="settings.notify_on_conflict" class="accent-yellow-500 w-4 h-4" />
            <span class="text-sm text-gray-400">Bisync conflicts detected</span>
            <span class="text-xs text-yellow-400/60 ml-auto">recommended</span>
          </label>
          <label class="flex items-center gap-3 cursor-pointer">
            <input type="checkbox" v-model="settings.notify_on_complete" class="accent-green-500 w-4 h-4" />
            <span class="text-sm text-gray-400">Sync completed successfully</span>
            <span class="text-xs text-gray-600 ml-auto">can be noisy</span>
          </label>
        </div>
      </div>

      <!-- Actions -->
      <div class="flex gap-3 pt-2">
        <button
          @click="save"
          class="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-500 transition"
          :disabled="saving"
        >
          {{ saving ? 'Saving...' : 'Save' }}
        </button>
        <button
          @click="testNotification"
          class="px-4 py-2 bg-gray-700 text-gray-300 rounded-lg text-sm hover:bg-gray-600 transition"
          :disabled="testing"
        >
          {{ testing ? 'Sending...' : 'Send Test' }}
        </button>
        <span v-if="statusMsg" class="text-xs self-center" :class="statusOk ? 'text-green-400' : 'text-red-400'">
          {{ statusMsg }}
        </span>
      </div>
    </div>

    <!-- How to setup -->
    <div class="bg-gray-900 rounded-lg border border-gray-800 p-6 max-w-xl">
      <h3 class="text-sm font-medium text-gray-300 mb-3">How to setup Telegram bot</h3>
      <ol class="text-xs text-gray-500 space-y-1.5 list-decimal list-inside">
        <li>Message <code class="text-gray-400">@BotFather</code> on Telegram</li>
        <li>Send <code class="text-gray-400">/newbot</code> and follow instructions</li>
        <li>Copy the bot token and paste above</li>
        <li>Message your new bot, then visit
          <code class="text-gray-400">https://api.telegram.org/bot&lt;TOKEN&gt;/getUpdates</code>
          to find your chat ID</li>
        <li>Click "Send Test" to verify</li>
      </ol>
    </div>
  </div>
</template>

<script setup lang="ts">
const api = useApi()

const settings = ref({
  telegram_bot_token: '',
  telegram_chat_id: '',
  notify_on_error: true,
  notify_on_complete: false,
  notify_on_conflict: true,
})
const saving = ref(false)
const testing = ref(false)
const statusMsg = ref('')
const statusOk = ref(false)

async function load() {
  try {
    const data = await api.get<any>('/api/notifications/settings')
    Object.assign(settings.value, data)
  } catch {}
}

async function save() {
  saving.value = true
  statusMsg.value = ''
  try {
    await api.put('/api/notifications/settings', settings.value)
    statusMsg.value = 'Saved'
    statusOk.value = true
  } catch {
    statusMsg.value = 'Error saving'
    statusOk.value = false
  } finally {
    saving.value = false
    setTimeout(() => { statusMsg.value = '' }, 3000)
  }
}

async function testNotification() {
  testing.value = true
  statusMsg.value = ''
  try {
    await save()
    const result = await api.post<any>('/api/notifications/test')
    statusMsg.value = result.ok ? 'Sent! Check Telegram' : (result.error || 'Failed')
    statusOk.value = !!result.ok
  } catch {
    statusMsg.value = 'Send failed'
    statusOk.value = false
  } finally {
    testing.value = false
    setTimeout(() => { statusMsg.value = '' }, 5000)
  }
}

onMounted(load)
</script>
