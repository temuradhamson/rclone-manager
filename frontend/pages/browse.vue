<template>
  <div class="h-[calc(100vh-120px)]">
    <ClientOnly>
      <VueFinder
        id="rclone-fm"
        :driver="driver"
        :features="features"
        theme="dark"
        locale="en"
      />
    </ClientOnly>
  </div>
</template>

<script setup lang="ts">
import { RemoteDriver } from 'vuefinder'

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
  createFile: false,
  save: false,
  preview: true,
  download: true,
}
</script>

<style>
.vuefinder {
  height: 100% !important;
  border-radius: 0.5rem;
  overflow: hidden;
}
</style>
