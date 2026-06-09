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
            <option value="horizontal_bar">📊 橫向長條圖</option>
            <option value="stacked_bar">📊 堆疊長條圖</option>
            <option value="line">📈 折線圖</option>
            <option value="pie">🥧 圓餅圖</option>
            <option value="doughnut">🍩 環形圖</option>
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
    <button class="btn-sh btn-sh-outline btn-sh-lg" @click="previewDashboard" :disabled="!store.generatedDashboardUrl">👁 預覽</button>
  </div>

  <!-- Progress bar -->
  <div v-if="generating" class="mt-3">
    <div class="progress-sh">
      <div class="progress-bar" :style="{width: progressPercent + '%'}"></div>
    </div>
    <p class="text-xs text-muted text-center mt-1">{{ progressText }}</p>
  </div>

  <!-- Add Chart Modal -->
  <div v-if="showAddChartModal" class="modal-overlay" @click.self="closeAddChartModal">
    <div class="modal-dialog modal-lg">
      <div class="card-sh">
        <div class="card-header flex items-center justify-between">
          <span class="font-medium text-sm">➕ 新增圖表</span>
          <button class="btn-sh btn-sh-ghost btn-sh-icon btn-sh-sm" @click="closeAddChartModal">✕</button>
        </div>
        <div class="card-body">
          <!-- Tab navigation -->
          <div class="flex gap-1 mb-4 border-b border-border">
            <button class="btn-sh btn-sh-sm px-4 py-2"
                    :class="addChartTab === 'csv' ? 'btn-sh-primary' : 'btn-sh-secondary'"
                    @click="addChartTab = 'csv'">
              📝 手動輸入 CSV
            </button>
            <button class="btn-sh btn-sh-sm px-4 py-2"
                    :class="addChartTab === 'dataset' ? 'btn-sh-primary' : 'btn-sh-secondary'"
                    @click="addChartTab = 'dataset'">
              📂 選擇現有資料集
            </button>
          </div>

          <!-- CSV Input Tab -->
          <div v-if="addChartTab === 'csv'">
            <div class="mb-3">
              <label class="text-xs text-muted mb-1 block">CSV 資料</label>
              <textarea class="input-sh text-sm" rows="6" v-model="csvText"
                        placeholder="請貼上 CSV 資料，例如：&#10;部門,月份,金額&#10;業務部,2024-01,850&#10;行銷部,2024-01,450&#10;研發部,2024-01,320"></textarea>
              <p class="text-xs text-muted mt-1">第一行需為標題列，支援逗號、分號、Tab 分隔</p>
            </div>
            <div class="mb-3">
              <label class="text-xs text-muted mb-1 block">分隔符號</label>
              <select class="input-sh select-sh text-sm" v-model="csvDelimiter">
                <option value=",">逗號 (,)</option>
                <option value=";">分號 (;)</option>
                <option value="\t">Tab (\t)</option>
              </select>
            </div>
            <button class="btn-sh btn-sh-secondary btn-sh-sm" @click="parseCsv">解析 CSV</button>
            <div v-if="csvParseError" class="text-xs mt-2" style="color:var(--danger)">{{ csvParseError }}</div>
            <div v-if="csvParsed" class="mt-3 p-2" style="background:var(--bg-subtle);border-radius:var(--radius-sm)">
              <div class="text-xs text-muted mb-1">解析結果：{{ csvPreview.columns.length }} 欄 × {{ csvPreview.rows }} 列</div>
              <div class="text-xs">欄位：{{ csvPreview.columns.join(', ') }}</div>
            </div>
          </div>

          <!-- Dataset Selection Tab -->
          <div v-if="addChartTab === 'dataset'">
            <div class="mb-3">
              <label class="text-xs text-muted mb-1 block">選擇資料集</label>
              <select class="input-sh select-sh text-sm" v-model="selectedDataset" @change="onDatasetChange">
                <option value="">-- 請選擇 --</option>
                <option v-for="ds in availableDatasets" :key="ds.key" :value="ds.key">
                  {{ ds.file }} / {{ ds.sheet }} ({{ ds.columns.length }} 欄 × {{ ds.rows }} 列)
                </option>
              </select>
            </div>
            <div v-if="selectedDataset && datasetPreview">
              <div class="mb-3 p-2" style="background:var(--bg-subtle);border-radius:var(--radius-sm)">
                <div class="text-xs text-muted mb-1">{{ selectedDatasetLabel }}</div>
                <div class="text-xs">欄位：{{ datasetPreview.columns.join(', ') }}</div>
              </div>
            </div>
          </div>

          <!-- Chart Configuration (shown after data source selected) -->
          <div v-if="csvParsed || (selectedDataset && datasetPreview)" class="mt-4 pt-4 border-t border-border">
            <div class="row g-2 mb-3">
              <div class="col-md-4">
                <label class="text-xs text-muted mb-1 block">圖表標題</label>
                <input class="input-sh text-sm" v-model="newChartTitle" placeholder="輸入圖表標題">
              </div>
              <div class="col-md-4">
                <label class="text-xs text-muted mb-1 block">圖表類型</label>
                <select class="input-sh select-sh text-sm" v-model="newChartType">
                  <option value="bar">📊 長條圖</option>
                  <option value="horizontal_bar">📊 橫向長條圖</option>
                  <option value="stacked_bar">📊 堆疊長條圖</option>
                  <option value="line">📈 折線圖</option>
                  <option value="pie">🥧 圓餅圖</option>
                  <option value="doughnut">🍩 環形圖</option>
                  <option value="scatter">✨ 散點圖</option>
                  <option value="radar">🕸 雷達圖</option>
                  <option value="treemap">🗂 Treemap</option>
                </select>
              </div>
              <div class="col-md-4">
                <label class="text-xs text-muted mb-1 block">位置</label>
                <select class="input-sh select-sh text-sm" v-model="newChartPosition">
                  <option value="top-left">左上</option>
                  <option value="top-right">右上</option>
                  <option value="bottom-left">左下</option>
                  <option value="bottom-right">右下</option>
                  <option value="full-width">全寬</option>
                </select>
              </div>
            </div>
            <div class="row g-2">
              <div class="col-md-6">
                <label class="text-xs text-muted mb-1 block">X 軸欄位</label>
                <select class="input-sh select-sh text-sm" v-model="newChartXCol">
                  <option v-for="col in currentDataColumns" :key="col" :value="col">{{ col }}</option>
                </select>
              </div>
              <div class="col-md-6">
                <label class="text-xs text-muted mb-1 block">Y 軸欄位</label>
                <select class="input-sh select-sh text-sm" v-model="newChartYCol">
                  <option v-for="col in currentDataColumns" :key="col" :value="col">{{ col }}</option>
                </select>
              </div>
            </div>
            <div class="flex justify-end gap-2 mt-4">
              <button class="btn-sh btn-sh-secondary btn-sh-sm" @click="closeAddChartModal">取消</button>
              <button class="btn-sh btn-sh-primary btn-sh-sm" @click="confirmAddChart" :disabled="!newChartTitle || !newChartXCol || !newChartYCol">新增圖表</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useDashboardStore } from '../stores/dashboard'
import axios from 'axios'

const router = useRouter()
const route = useRoute()
const store = useDashboardStore()
const generating = ref(false)
const progressText = ref('')
const progressPercent = ref(0)

// Add Chart Modal state
const showAddChartModal = ref(false)
const addChartTab = ref('csv')
const csvText = ref('')
const csvDelimiter = ref(',')
const csvParsed = ref(false)
const csvPreview = ref(null)
const csvParseError = ref('')
const selectedDataset = ref('')
const datasetPreview = ref(null)
const selectedDatasetLabel = ref('')
const newChartTitle = ref('')
const newChartType = ref('bar')
const newChartPosition = ref('bottom-left')
const newChartXCol = ref('')
const newChartYCol = ref('')

const progressSteps = [
  { text: '正在分析資料結構…', pct: 15 },
  { text: '正在建議圖表配置…', pct: 30 },
  { text: '正在生成 ECharts 圖表…', pct: 55 },
  { text: '正在渲染 Bootstrap 佈局…', pct: 75 },
  { text: '正在執行語法檢查…', pct: 90 },
]

function typeIcon(type) {
  const m = { bar: '📊', horizontal_bar: '📊', stacked_bar: '📊', line: '📈', pie: '🥧', doughnut: '🍩', radar: '🕸', scatter: '✨', treemap: '🗂' }
  return m[type] || '📊'
}
function typeLabel(type) {
  const m = { bar: '長條圖', horizontal_bar: '橫向長條圖', stacked_bar: '堆疊長條圖', line: '折線圖', pie: '圓餅圖', doughnut: '環形圖', radar: '雷達圖', scatter: '散點圖', treemap: 'Treemap' }
  return m[type] || type
}
function typeBadgeClass(type) {
  const m = { bar: 'badge-sh-info', horizontal_bar: 'badge-sh-info', stacked_bar: 'badge-sh-info', line: 'badge-sh-success', pie: 'badge-sh-warning', doughnut: 'badge-sh-warning', radar: 'badge-sh-default', scatter: 'badge-sh-info', treemap: 'badge-sh-default' }
  return m[type] || 'badge-sh-default'
}

function availableCols(s) {
  const file = store.files.find(f => f.filename === s.source?.file)
  const sheet = file?.sheets?.find(sh => sh.name === s.source?.sheet)
  return sheet?.columns || []
}

// Dataset options for modal
const availableDatasets = computed(() => {
  const datasets = []
  for (const file of store.files) {
    for (const sheet of file.sheets || []) {
      if (!sheet.error) {
        datasets.push({
          key: `${file.filename}/${sheet.name}`,
          file: file.filename,
          sheet: sheet.name,
          columns: sheet.columns,
          rows: sheet.rows
        })
      }
    }
  }
  return datasets
})

const currentDataColumns = computed(() => {
  if (csvParsed.value && csvPreview.value) {
    return csvPreview.value.columns
  }
  if (selectedDataset.value && datasetPreview.value) {
    return datasetPreview.value.columns
  }
  return []
})

function toggleConfirm(idx) {
  store.pushUndo({ suggestions: store.suggestions, selectedSheets: store.selectedSheets, userRefinements: store.userRefinements })
  store.suggestions[idx]._confirmed = !store.suggestions[idx]._confirmed
}

function removeSuggestion(idx) {
  store.pushUndo({ suggestions: store.suggestions, selectedSheets: store.selectedSheets, userRefinements: store.userRefinements })
  store.suggestions.splice(idx, 1)
}

function addChart() {
  showAddChartModal.value = true
  addChartTab.value = 'csv'
  resetAddChartForm()
}

function closeAddChartModal() {
  showAddChartModal.value = false
  resetAddChartForm()
}

function resetAddChartForm() {
  addChartTab.value = 'csv'
  csvText.value = ''
  csvDelimiter.value = ','
  csvParsed.value = false
  csvPreview.value = null
  csvParseError.value = ''
  selectedDataset.value = ''
  datasetPreview.value = null
  selectedDatasetLabel.value = ''
  newChartTitle.value = ''
  newChartType.value = 'bar'
  newChartPosition.value = 'bottom-left'
  newChartXCol.value = ''
  newChartYCol.value = ''
}

async function parseCsv() {
  csvParseError.value = ''
  if (!csvText.value.trim()) {
    csvParseError.value = '請輸入 CSV 資料'
    return
  }
  try {
    const res = await axios.post('/api/parse_csv', {
      csv_text: csvText.value,
      delimiter: csvDelimiter.value
    })
    csvPreview.value = res.data
    csvParsed.value = true
    newChartXCol.value = csvPreview.value.columns[0] || ''
    newChartYCol.value = csvPreview.value.columns[1] || ''
    newChartTitle.value = 'CSV 匯入圖表'
  } catch (e) {
    csvParseError.value = e.response?.data?.error || '解析失敗：' + e.message
  }
}

function onDatasetChange() {
  if (!selectedDataset.value) {
    datasetPreview.value = null
    selectedDatasetLabel.value = ''
    return
  }
  const ds = availableDatasets.value.find(d => d.key === selectedDataset.value)
  if (ds) {
    // Find the full sheet data
    const [fileKey, sheetKey] = selectedDataset.value.split('/')
    const file = store.files.find(f => f.filename === fileKey)
    const sheet = file?.sheets?.find(sh => sh.name === sheetKey)
    if (sheet) {
      datasetPreview.value = {
        columns: sheet.columns,
        rows: sheet.rows,
        dtypes: sheet.dtypes,
        stats: sheet.stats,
        preview: sheet.data_json_compatible || sheet.data
      }
      selectedDatasetLabel.value = `${ds.file} / ${ds.sheet}`
      newChartXCol.value = sheet.columns[0] || ''
      newChartYCol.value = sheet.columns[1] || ''
      newChartTitle.value = `${ds.sheet} 圖表`
    }
  }
}

function confirmAddChart() {
  if (!newChartTitle.value || !newChartXCol.value || !newChartYCol.value) return
  
  let source, fullData
  if (csvParsed.value && csvPreview.value) {
    source = { file: 'manual_csv_input', sheet: 'CSV輸入' }
    fullData = csvPreview.value.full_data
  } else if (selectedDataset.value && datasetPreview.value) {
    const [fileKey, sheetKey] = selectedDataset.value.split('/')
    source = { file: fileKey, sheet: sheetKey }
    fullData = datasetPreview.value.preview
  }
  
  store.pushUndo({ suggestions: store.suggestions, selectedSheets: store.selectedSheets, userRefinements: store.userRefinements })
  store.suggestions.push({
    id: `custom_${Date.now()}`,
    title: newChartTitle.value,
    type: newChartType.value,
    source: source,
    xColumn: newChartXCol.value,
    yColumn: newChartYCol.value,
    position: newChartPosition.value,
    description: '手動新增',
    _confirmed: true,
    _customData: fullData // Store custom data for generation
  })
  
  closeAddChartModal()
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
    store.generatedDashboardUrl = result.dashboard_url
  } catch (e) {
    progressText.value = '生成失敗：' + (e?.message || '未知錯誤')
  } finally {
    generating.value = false
  }
}

function previewDashboard() {
  if (store.generatedDashboardUrl) {
    window.open(store.generatedDashboardUrl, '_blank')
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
