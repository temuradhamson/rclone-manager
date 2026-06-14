import { VueFinderPlugin } from 'vuefinder'
// @ts-ignore - raw import bypasses PostCSS entirely
import cssText from 'vuefinder/dist/vuefinder.css?raw'

export default defineNuxtPlugin((nuxtApp) => {
  nuxtApp.vueApp.use(VueFinderPlugin)

  const style = document.createElement('style')
  style.textContent = cssText
  document.head.appendChild(style)
})
