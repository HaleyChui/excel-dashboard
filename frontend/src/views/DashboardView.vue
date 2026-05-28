<template>
<div class="dashboard-page">
  <!-- Toolbar -->
  <div class="dash-toolbar flex items-center justify-between">
    <div class="flex items-center gap-2">
      <router-link class="btn-sh btn-sh-secondary btn-sh-sm" :to="`/config/${store.sessionId}`">
        編輯配置
      </router-link>
      <button class="btn-sh btn-sh-secondary btn-sh-sm" @click="showTemplateModal = true">
        另存為模板
      </button>
    </div>
    <div class="flex items-center gap-2">
      <!-- Version switcher -->
      <div v-if="store.versions.length > 1" class="flex items-center gap-1 mr-2">
        <span class="text-xs text-muted">版本：</span>
        <button v-for="v in store.versions" :key="v.version"
                class="btn-sh btn-sh-sm"
                :class="v.version === currentVersion ? 'btn-sh-primary' : 'btn-sh-secondary'"
                @click="switchVersion(v.version)">
          v{{ v.version }}
        </button>
      </div>
      <button class="btn-sh btn-sh-secondary btn-sh-sm" @click="isDark = !isDark">
        {{ isDark ? '淺色' : '深色' }}
      </button>
      <button class="btn-sh btn-sh-secondary btn-sh-sm" @click="exportPDF">PDF</button>
      <button class="btn-sh btn-sh-primary btn-sh-sm" @click="copyLink">分享</button>
    </div>
  </div>

  <!-- Dashboard iframe -->
  <iframe v-if="dashboardUrl"
          :src="dashboardUrl"
          class="dash-iframe"
          :class="{'dark-frame': isDark}"
          frameborder="0"
          allowfullscreen></iframe>

  <!-- Loading -->
  <div v-else class="dash-loading flex items-center justify-center">
    <p class="text-muted">載入中…</p>
  </div>

  <!-- Template modal -->
  <div v-if="showTemplateModal" class="modal-overlay" @click.self="showTemplateModal=false">
    <div class="modal-dialog">
      <div class="card-sh">
        <div class="card-header flex items-center justify-between">
          <span class="font-medium text-sm">另存為模板</span>
          <button class="btn-sh btn-sh-ghost btn-sh-icon btn-sh-sm" @click="showTemplateModal=false">✕</button>
        </div>
        <div class="card-body">
          <input class="input-sh" v-model="templateName" placeholder="模板名稱">
          <div class="flex justify-end gap-2 mt-3">
            <button class="btn-sh btn-sh-secondary btn-sh-sm" @click="showTemplateModal=false">取消</button>
            <button class="btn-sh btn-sh-primary btn-sh-sm" @click="confirmSaveTemplate">儲存</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useDashboardStore } from '../stores/dashboard'
import axios from 'axios'

const route = useRoute()
const store = useDashboardStore()
const currentVersion = ref(1)
const isDark = ref(true)
const showTemplateModal = ref(false)
const templateName = ref('')

const dashboardUrl = computed(() => {
  if (!store.sessionId) return ''
  return `/dashboard/${store.sessionId}/${currentVersion.value}`
})

onMounted(async () => {
  store.sessionId = route.params.sessionId
  if (route.params.version) {
    currentVersion.value = parseInt(route.params.version)
  }
  await store.fetchVersions()
})

async function copyLink() {
  const url = `${window.location.origin}/dashboard/${store.sessionId}/${currentVersion.value}`
  await navigator.clipboard.writeText(url)
  alert('戰情表連結已複製')
}

async function switchVersion(v) {
  currentVersion.value = v
}

function exportPDF() {
  // Trigger print inside iframe
  const iframe = document.querySelector('.dash-iframe')
  if (iframe && iframe.contentWindow) {
    iframe.contentWindow.print()
  } else {
    window.print()
  }
}

async function confirmSaveTemplate() {
  await axios.post('/api/templates', {
    name: templateName.value,
    config: { sessionId: store.sessionId, version: currentVersion.value }
  })
  showTemplateModal.value = false
  alert('模板已儲存')
}
</script>

<style scoped>
.dashboard-page { height: calc(100vh - 48px); display: flex; flex-direction: column; }
.dash-toolbar {
  background: var(--bg);
  border-bottom: 1px solid var(--border);
  padding: 8px 16px;
  flex-shrink: 0;
}
.dash-iframe {
  flex: 1;
  width: 100%;
  border: none;
  background: #fff;
}
.dash-iframe.dark-frame { background: #0D0D0D; }
.dash-loading { flex: 1; }
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.5);
  display: flex; align-items: center; justify-content: center;
  z-index: 1050;
}
.modal-dialog { width: 360px; }
</style>
