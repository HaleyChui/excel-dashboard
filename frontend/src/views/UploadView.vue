<template>
<div class="container py-4" style="max-width:760px">

  <!-- Header -->
  <div class="mb-4">
    <h2 class="font-semibold" style="font-size:var(--text-xl)">📤 上傳 Excel 檔案</h2>
    <p class="text-sm text-muted mt-1">支援 .xlsx / .csv，可一次上傳多個檔案</p>
  </div>

  <!-- Upload Zone -->
  <div class="upload-zone"
       @dragover.prevent="dragOver=true"
       @dragleave.prevent="dragOver=false"
       @drop.prevent="onDrop"
       @click="$refs.fileInput.click()"
       :class="{'upload-zone--active': dragOver}">
    <div class="upload-icon mb-3">
      <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor"
           stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"
           style="color:var(--fg-muted)">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
        <polyline points="17 8 12 3 7 8"/>
        <line x1="12" y1="3" x2="12" y2="15"/>
      </svg>
    </div>
    <p class="font-medium text-sm mb-1">點擊或拖曳檔案到這裡</p>
    <p class="text-xs text-muted">可一次選取多個 .xlsx / .csv 檔案</p>
    <input ref="fileInput" type="file" multiple accept=".xlsx,.xls,.csv"
           @change="onFileSelect" hidden>
    <button class="btn-sh btn-sh-secondary btn-sh-sm mt-3">選擇檔案</button>
  </div>

  <!-- Uploading state -->
  <div v-if="uploading" class="mt-3">
    <div class="progress-sh">
      <div class="progress-bar" :style="{width: uploadProgress+'%'}"></div>
    </div>
    <p class="text-xs text-muted text-center mt-1">正在上傳…</p>
  </div>

  <!-- File list -->
  <div v-if="store.files.length > 0" class="mt-4">

    <div class="flex items-center justify-between mb-2">
      <span class="text-sm font-medium">已上傳的檔案</span>
      <span class="badge-sh badge-sh-default">{{ store.files.length }} 個檔案</span>
    </div>

    <div v-for="file in store.files" :key="file.filename" class="card-sh mb-2">
      <div class="card-header flex items-center justify-between"
           @click="file._expanded = !file._expanded" style="cursor:pointer">
        <div class="flex items-center gap-2">
          <span class="text-xs" style="color:var(--fg-muted)">
            {{ file._expanded ? '▼' : '▶' }}
          </span>
          <svg width="16" height="18" viewBox="0 0 16 18" fill="none"
               style="color:#16A34A;flex-shrink:0">
            <path d="M2 2h8l4 4v12H2V2z" fill="currentColor" opacity=".15"/>
            <path d="M10 2v4h4" stroke="currentColor" stroke-width="1.5" fill="none"/>
            <text x="8" y="13" text-anchor="middle" font-size="6" font-weight="700"
                  fill="currentColor">XLS</text>
          </svg>
          <span class="font-medium text-sm truncate" style="max-width:260px">{{ file.filename }}</span>
          <span class="badge-sh badge-sh-default">{{ file.sheets?.length || 0 }} Sheet</span>
        </div>
        <button class="btn-sh btn-sh-ghost btn-sh-icon btn-sh-sm" @click.stop="removeFile(file.filename)">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
               stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>

      <div v-if="file._expanded" class="card-body" style="padding-top:0">
        <div v-for="sheet in file.sheets" :key="sheet.name"
             class="sheet-row flex items-center gap-2 py-2 px-2"
             style="border-radius:var(--radius-sm)">
          <input type="checkbox" class="checkbox-sh"
                 :checked="isSheetSelected(file.filename, sheet.name)"
                 @change="toggleSheet(file.filename, sheet.name)">
          <span class="text-sm font-medium">{{ sheet.name }}</span>
          <span class="badge-sh badge-sh-default">{{ sheet.columns?.length || 0 }}欄 × {{ sheet.rows || 0 }}列</span>
          <div v-if="sheet.error" class="text-xs" style="color:var(--danger)">{{ sheet.error }}</div>
          <div v-if="sheet.columns" class="text-xs text-muted truncate ml-auto" style="max-width:200px">
            {{ sheet.columns.join('、') }}
          </div>
        </div>
      </div>
    </div>

    <!-- Actions -->
    <div class="flex items-center justify-between mt-4">
      <button class="btn-sh btn-sh-ghost btn-sh-sm" @click="clearAll">清除全部</button>
      <button class="btn-sh btn-sh-primary btn-sh-lg"
              :disabled="store.selectedSheets.length === 0 || analyzing"
              @click="startAnalysis">
        <span v-if="analyzing" class="flex items-center gap-2">
          <svg class="animate-spin" width="16" height="16" viewBox="0 0 24 24" fill="none"
               stroke="currentColor" stroke-width="2">
            <path d="M12 2v4m0 12v4M4.93 4.93l2.83 2.83m8.48 8.48 2.83 2.83M2 12h4m12 0h4M6.34 17.66l2.83-2.83m8.48-8.48 2.83-2.83"/>
          </svg>
          分析中…
        </span>
        <span v-else>🤖 開始分析 <span v-if="store.selectedSheets.length > 0">({{ store.selectedSheets.length }})</span></span>
      </button>
    </div>
  </div>

</div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useDashboardStore } from '../stores/dashboard'

const router = useRouter()
const store = useDashboardStore()
const fileInput = ref(null)
const dragOver = ref(false)
const uploading = ref(false)
const uploadProgress = ref(0)
const analyzing = ref(false)

function onFileSelect(e) { handleFiles(e.target.files) }
function onDrop(e) { dragOver.value = false; handleFiles(e.dataTransfer.files) }

async function handleFiles(fileList) {
  if (!fileList || fileList.length === 0) return
  uploading.value = true
  uploadProgress.value = 0
  const interval = setInterval(() => {
    uploadProgress.value = Math.min(uploadProgress.value + 15, 90)
  }, 200)
  try {
    await store.uploadFiles(fileList)
    uploadProgress.value = 100
  } finally {
    clearInterval(interval)
    uploading.value = false
  }
}

function isSheetSelected(filename, sheetName) {
  return store.selectedSheets.some(s => s.filename === filename && s.sheetName === sheetName)
}

function toggleSheet(filename, sheetName) {
  const idx = store.selectedSheets.findIndex(s => s.filename === filename && s.sheetName === sheetName)
  if (idx >= 0) store.selectedSheets.splice(idx, 1)
  else store.selectedSheets.push({ filename, sheetName })
}

function removeFile(filename) {
  store.files = store.files.filter(f => f.filename !== filename)
  store.selectedSheets = store.selectedSheets.filter(s => s.filename !== filename)
}

function clearAll() {
  store.files = []
  store.selectedSheets = []
}

async function startAnalysis() {
  analyzing.value = true
  try {
    await store.analyzeData()
    router.push(`/config/${store.sessionId}`)
  } finally {
    analyzing.value = false
  }
}
</script>

<style scoped>
.upload-zone {
  border: 2px dashed var(--border);
  border-radius: var(--radius-lg);
  padding: 48px 24px;
  text-align: center;
  cursor: pointer;
  transition: all var(--duration-normal) var(--ease);
  background: var(--bg);
}
.upload-zone:hover,
.upload-zone--active {
  border-color: var(--accent);
  background: var(--bg-subtle);
}
.upload-icon {
  transition: transform var(--duration-fast) var(--ease);
}
.upload-zone:hover .upload-icon {
  transform: translateY(-2px);
}
.sheet-row:hover {
  background: var(--bg-hover);
}
</style>
