import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

const API = '/api'

export const useDashboardStore = defineStore('dashboard', () => {
  const sessionId = ref(null)
  const files = ref([])           // 已上傳的檔案清單
  const selectedSheets = ref([])  // user 勾選的 {filename, sheetName}
  const suggestions = ref([])     // AI 建議的圖表
  const userRefinements = ref('') // user 文字補充
  const versions = ref([])        // 版本歷史
  const generatedDashboardUrl = ref('') // 生成的儀表板 URL
  const undoStack = ref([])       // Undo/Redo
  const redoStack = ref([])

  // ── Upload ──
  async function uploadFiles(fileList) {
    const form = new FormData()
    if (!sessionId.value) {
      sessionId.value = crypto.randomUUID()
    }
    form.append('session_id', sessionId.value)
    for (const f of fileList) {
      form.append('files', f)
    }
    const { data } = await axios.post(`${API}/upload`, form)
    sessionId.value = data.session_id
    files.value = data.files
    return data
  }

  // ── AI Analyze ──
  async function analyzeData() {
    const { data } = await axios.post(`${API}/analyze`, {
      session_id: sessionId.value,
      selections: selectedSheets.value
    })
    suggestions.value = data.suggestions
    return data
  }

  // ── Generate ──
  async function generateDashboard(refinements = '') {
    const { data } = await axios.post(`${API}/generate`, {
      session_id: sessionId.value,
      selections: selectedSheets.value,
      refinements
    })
    versions.value.push(data.version)
    generatedDashboardUrl.value = data.dashboard_url
    return data
  }

  // ── Regenerate single component ──
  async function regenerateComponent(componentId, config) {
    const { data } = await axios.post(`${API}/regenerate/${componentId}`, config)
    return data
  }

  // ── Fetch versions ──
  async function fetchVersions() {
    if (!sessionId.value) return
    const { data } = await axios.get(`${API}/versions/${sessionId.value}`)
    versions.value = data.versions
  }

  // ── Undo/Redo ──
  function pushUndo(state) {
    undoStack.value.push(JSON.parse(JSON.stringify(state)))
    redoStack.value = []
  }
  function undo() {
    if (undoStack.value.length === 0) return null
    redoStack.value.push(JSON.parse(JSON.stringify({
      suggestions: suggestions.value,
      selectedSheets: selectedSheets.value,
      userRefinements: userRefinements.value
    })))
    const prev = undoStack.value.pop()
    suggestions.value = prev.suggestions
    selectedSheets.value = prev.selectedSheets
    userRefinements.value = prev.userRefinements || ''
    return prev
  }
  function redo() {
    if (redoStack.value.length === 0) return null
    undoStack.value.push(JSON.parse(JSON.stringify({
      suggestions: suggestions.value,
      selectedSheets: selectedSheets.value,
      userRefinements: userRefinements.value
    })))
    const next = redoStack.value.pop()
    suggestions.value = next.suggestions
    selectedSheets.value = next.selectedSheets
    userRefinements.value = next.userRefinements || ''
    return next
  }

  return {
    sessionId, files, selectedSheets, suggestions,
    userRefinements, versions, generatedDashboardUrl, undoStack, redoStack,
    uploadFiles, analyzeData, generateDashboard,
    regenerateComponent, fetchVersions,
    pushUndo, undo, redo
  }
})