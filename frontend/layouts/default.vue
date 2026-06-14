<template>
  <div class="min-h-screen flex">
    <LayoutAppSidebar />
    <main class="flex-1 ml-64">
      <LayoutAppHeader />
      <div class="p-6">
        <slot />
      </div>
    </main>
  </div>
</template>
