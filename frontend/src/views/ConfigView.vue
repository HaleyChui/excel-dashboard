<template>
<div class="container py-4" style="max-width:960px">

  <!-- Header -->
  <div class="flex items-center justify-between mb-4">
    <div>
      <h2 class="font-semibold" style="font-size:var(--text-xl)">🎨 圖表配置</h2>
      <p class="text-sm text-muted mt-1">AI 建議的圖表配對，可手動調整</p>
    </div>
    <div class="flex items-center gap-2">
      <button class="btn-sh btn-sh-secondary btn-sh-sm" @click="doUndo"
              :disabled="store.undoStack.length === 0">↩ 復原</button>
      <button class="btn-sh btn-sh-secondary btn-sh-sm" @click="doRedo"
              :disabled="store.redoStack.length === 0">↪ 重做</button>
    </div>
  </div>

  <!-- Empty state -->
  <div v-if="store.suggestions.length === 0" class="card-sh text-center py-5">
    <p class="text-muted text-sm">尚無圖表建議，請先上傳檔案並分析</p>
    <router-link to="/" class="btn-sh btn-sh-primary btn-sh-sm mt-3">← 回上傳頁</router-link>
  </div>

  <!-- Suggestion cards -->
  <div v-for="(s, idx) in store.suggestions" :key="s.id" class="card-sh mb-3 suggestion-card">
    <div class="card-body">
      <div class="flex items-center justify-between mb-3">
        <div class="flex items-center gap-2">
          <span class="badge-sh" :class="typeBadgeClass(s.type)">{{ typeIcon(s.type) }} {{ typeLabel(s.type) }}</span>
          <span class="font-medium text-sm">{{ s.title }}</span>
        </div>
        <div class="flex items-center gap-1">
          <button class="btn-sh btn-sh-sm"
                  :class="s._confirmed ? 'btn-sh-primary' : 'btn-sh-secondary'"
                  @click="toggleConfirm(idx)">
            {{ s._confirmed ? '✓ 已確認' : '確認' }}
          </button>
          <button class="btn-sh btn-sh-ghost btn-sh-icon btn-sh-sm" @click="removeSuggestion(idx)">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                 stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>
      </div>

      <div class="row g-2">
        <div class="col-md-3">
          <label class="text-xs text-muted mb-1 block">資料來源</label>
          <div class="input-sh text-xs" style="background:var(--bg-subtle);padding:6px 10px">
            {{ s.source?.file }} <span class="text-muted">/</span> {{ s.source?.sheet }}
          </div>
        </div>
        <div class="col-md-2">
          <label class="text-xs text-muted mb-1 block">圖表類型</label>
          <select class="input-sh select-sh text-sm" v-model="s.type" @change="onChange(idx)">
            <option value="bar">📊 長條圖</option>
            <option value="line">📈 折線圖</option>
            <option value="pie">🥧 圓餅圖</option>
            <option value="scatter">✨ 散點圖</option>
            <option value="radar">🕸 雷達圖</option>
            <option value="treemap">🗂 Treemap</option>
          </select>
        </div>
        <div class="col-md-2">
          <label class="text-xs text-muted mb-1 block">X 軸</label>
          <select class="input-sh select-sh text-sm" v-model="s.xColumn" @change="onChange(idx)">
            <option v-for="col in availableCols(s)" :key="col" :value="col">{{ col }}</option>
          </select>
        </div>
        <div class="col-md-2">
          <label class="text-xs text-muted mb-1 block">Y 軸</label>
          <select class="input-sh select-sh text-sm" v-model="s.yColumn" @change="onChange(idx)">
            <option v-for="col in availableCols(s)" :key="col" :value="col">{{ col }}</option>
          </select>
        </div>
        <div class="col-md-3">
          <label class="text-xs text-muted mb-1 block">位置</label>
          <select class="input-sh select-sh text-sm" v-model="s.position" @change="onChange(idx)">
            <option value="top-left">左上</option>
            <option value="top-right">右上</option>
            <option value="bottom-left">左下</option>
            <option value="bottom-right">右下</option>
            <option value="full-width">全寬</option>
          </select>
        </div>
      </div>
      <div class="text-xs text-muted mt-2">{{ s.description }}</div>
    </div>
  </div>

  <!-- Add chart -->
  <div class="text-center mb-4" v-if="store.suggestions.length > 0">
    <button class="btn-sh btn-sh-secondary" @click="addChart">＋ 新增圖表</button>
  </div>

  <!-- User refinements -->
  <div class="card-sh mb-4" v-if="store.suggestions.length > 0">
    <div class="card-body">
      <label class="text-sm font-medium mb-2 block">✏️ 補充需求</label>
      <textarea class="input-sh text-sm" rows="2"
                v-model="store.userRefinements"
                placeholder="例如：把左上長條圖改成堆疊長條圖、全部改用深色主題…"></textarea>
    </div>
  </div>

  <!-- Generate -->
  <div class="flex items-center justify-between" v-if="store.suggestions.length > 0">
    <router-link class="btn-sh btn-sh-secondary" to="/">← 回上傳頁</router-link>
    <button class="btn-sh btn-sh-primary btn-sh-lg" @click="generate" :disabled="generating">
      <span v-if="generating" class="flex items-center gap-2">
        <svg class="animate-spin" width="16" height="16" viewBox="0 0 24 24" fill="none"
             stroke="currentColor" stroke-width="2">
          <path d="M12 2v4m0 12v4M4.93 4.93l2.83 2.83m8.48 8.48 2.83 2.83M2 12h4m12 0h4M6.34 17.66l2.83-2.83m8.48-8.48 2.83-2.83"/>
        </svg>
        {{ progressText }}
      </span>
      <span v-else>🚀 生成戰情表</span>
    </button>
  </div>

  <!-- Progress bar -->
  <div v-if="generating" class="mt-3">
    <div class="progress-sh">
      <div class="progress-bar" :style="{width: progressPercent+'%'}"></div>
    </div>
    <p class="text-xs text-muted text-center mt-1">{{ progressText }}</p>
  </div>

</div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useDashboardStore } from '../stores/dashboard'

const router = useRouter()
const route = useRoute()
const store = useDashboardStore()
const generating = ref(false)
const progressText = ref('')
const progressPercent = ref(0)

const progressSteps = [
  { text: '正在分析資料結構…', pct: 15 },
  { text: '正在建議圖表配置…', pct: 30 },
  { text: '正在生成 ECharts 圖表…', pct: 55 },
  { text: '正在渲染 Bootstrap 佈局…', pct: 75 },
  { text: '正在執行語法檢查…', pct: 90 },
]

function typeIcon(type) {
  const m = { bar: '📊', line: '📈', pie: '🥧', radar: '🕸', scatter: '✨', treemap: '🗂' }
  return m[type] || '📊'
}
function typeLabel(type) {
  const m = { bar: '長條圖', line: '折線圖', pie: '圓餅圖', radar: '雷達圖', scatter: '散點圖', treemap: 'Treemap' }
  return m[type] || type
}
function typeBadgeClass(type) {
  const m = { bar: 'badge-sh-info', line: 'badge-sh-success', pie: 'badge-sh-warning',
              radar: 'badge-sh-default', scatter: 'badge-sh-info', treemap: 'badge-sh-default' }
  return m[type] || 'badge-sh-default'
}

function availableCols(s) {
  const file = store.files.find(f => f.filename === s.source?.file)
  const sheet = file?.sheets?.find(sh => sh.name === s.source?.sheet)
  return sheet?.columns || []
}

function toggleConfirm(idx) {
  store.pushUndo({ suggestions: store.suggestions, selectedSheets: store.selectedSheets, userRefinements: store.userRefinements })
  store.suggestions[idx]._confirmed = !store.suggestions[idx]._confirmed
}

function removeSuggestion(idx) {
  store.pushUndo({ suggestions: store.suggestions, selectedSheets: store.selectedSheets, userRefinements: store.userRefinements })
  store.suggestions.splice(idx, 1)
}

function addChart() {
  store.pushUndo({ suggestions: store.suggestions, selectedSheets: store.selectedSheets, userRefinements: store.userRefinements })
  store.suggestions.push({
    id: `custom_${Date.now()}`,
    title: '新圖表',
    type: 'bar',
    source: store.selectedSheets[0] || {},
    xColumn: '',
    yColumn: '',
    position: 'bottom-left',
    description: '手動新增',
    _confirmed: false
  })
}

function onChange(idx) {
  const s = store.suggestions[idx]
  s.id = `${s.source?.file || ''}_${s.source?.sheet || ''}_${s.type}_${idx}`.replace(/[.\s/]/g, '_')
}

function doUndo() { store.undo() }
function doRedo() { store.redo() }

async function generate() {
  generating.value = true
  progressPercent.value = 0
  for (const step of progressSteps) {
    progressText.value = step.text
    progressPercent.value = step.pct
    await new Promise(r => setTimeout(r, 600))
  }
  try {
    const result = await store.generateDashboard(store.userRefinements)
    progressPercent.value = 100
    progressText.value = '完成！'
    // 在新分頁開啟 dashboard，不影響目前頁面
    window.open(result.dashboard_url, '_blank')
  } catch (e) {
    progressText.value = '生成失敗：' + (e?.message || '未知錯誤')
  } finally {
    generating.value = false
  }
}
</script>

<style scoped>
.suggestion-card {
  transition: box-shadow var(--duration-fast) var(--ease);
}
.suggestion-card:hover {
  box-shadow: var(--shadow-md);
}
.block { display: block; }
</style>
