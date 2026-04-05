<template>
  <div class="h-[calc(100vh-120px)]">
    <VueFinder
      :driver="driver"
      :features="features"
      theme="dark"
      locale="en"
    />
  </div>
</template>

<script setup lang="ts">
import { VueFinder, RemoteDriver } from 'vuefinder'
import 'vuefinder/dist/vuefinder.css'

const config = useRuntimeConfig()

const driver = new RemoteDriver({
  baseURL: config.public.apiBase + '/api/fm',
  url: {
    list: '/list',
    upload: '/upload',
    delete: '/delete',
    rename: '/rename',
    copy: '/copy',
    move: '/move',
    archive: '/archive',
    unarchive: '/unarchive',
    createFile: '/createFile',
    createFolder: '/createFolder',
    preview: '/preview',
    download: '/download',
    search: '/search',
    save: '/save',
  },
})

const features = {
  archive: false,
  unarchive: false,
  preview: false,
  createFile: false,
  save: false,
}
</script>

<style>
/* Override VueFinder styles to match our dark theme */
.vuefinder {
  height: 100% !important;
  border-radius: 0.5rem;
  overflow: hidden;
}
</style>
