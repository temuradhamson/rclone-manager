import { VueFinderPlugin } from 'vuefinder'

export default defineNuxtPlugin(async (nuxtApp) => {
  nuxtApp.vueApp.use(VueFinderPlugin)

  // Dynamically inject VueFinder CSS to bypass Tailwind PostCSS processing
  const cssModule = await import('vuefinder/dist/vuefinder.css?inline')
  const style = document.createElement('style')
  style.textContent = cssModule.default
  document.head.appendChild(style)
})
