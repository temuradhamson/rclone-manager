export default defineNuxtConfig({
  compatibilityDate: '2025-06-01',
  modules: [
    '@nuxtjs/tailwindcss',
    '@pinia/nuxt',
    '@vueuse/nuxt',
  ],
  css: ['~/assets/css/main.css'],
  postcss: {
    plugins: {
      tailwindcss: {},
      autoprefixer: {},
    },
  },
  ssr: false,
  devtools: { enabled: false },
  runtimeConfig: {
    public: {
      apiBase: 'http://127.0.0.1:8001',
      wsBase: 'ws://127.0.0.1:8001',
    },
  },
})
