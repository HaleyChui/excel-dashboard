<template>
<div id="app-shell" :data-theme="isDark ? 'dark' : 'light'">
  <!-- Top Nav -->
  <nav class="top-nav flex items-center justify-between">
    <div class="flex items-center gap-3">
      <router-link to="/" class="font-semibold text-lg flex items-center gap-2" style="text-decoration:none;color:var(--fg)">
        <span style="font-size:20px">📊</span>
        <span class="hidden sm:inline">戰情表生成器</span>
      </router-link>
    </div>
    <div class="flex items-center gap-2">
      <router-link class="btn-sh btn-sh-ghost btn-sh-sm" to="/templates">📁 模板</router-link>
      <button class="btn-sh btn-sh-ghost btn-sh-icon btn-sh-sm" @click="isDark = !isDark"
              title="切換主題">
        <span v-if="isDark">☀️</span><span v-else>🌙</span>
      </button>
    </div>
  </nav>

  <!-- Main Content -->
  <main class="main-content">
    <router-view v-slot="{ Component }">
      <keep-alive>
        <component :is="Component" />
      </keep-alive>
    </router-view>
  </main>
</div>
</template>

<script setup>
import { ref, watch } from 'vue'
import './style.css'

const isDark = ref(false)

// Restore theme
const saved = localStorage.getItem('dash-theme')
if (saved === 'dark') isDark.value = true

// Persist theme preference
watch(isDark, (v) => {
  localStorage.setItem('dash-theme', v ? 'dark' : 'light')
})
</script>

<style>
.top-nav {
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--bg);
  border-bottom: 1px solid var(--border);
  padding: 10px 20px;
  backdrop-filter: blur(8px);
  transition: background var(--duration-normal) var(--ease),
              border-color var(--duration-normal) var(--ease);
}
.main-content {
  max-width: 1280px;
  margin: 0 auto;
  padding: 24px 16px;
}
@media (max-width: 640px) {
  .main-content { padding: 16px 12px; }
}
</style>
