<template>
  <div class="container py-4">
    <h2 class="mb-4">📁 自定義模板</h2>

    <div v-if="templates.length === 0" class="text-center text-muted py-5">
      <p class="fs-5">尚無儲存的模板</p>
      <p>在戰情表頁面點「另存為模板」即可新增</p>
    </div>

    <div v-else class="row">
      <div v-for="tpl in templates" :key="tpl.id" class="col-md-4 mb-3">
        <div class="card">
          <div class="card-body">
            <h5 class="card-title">{{ tpl.name }}</h5>
            <p class="card-text text-muted small">
              建立於 {{ tpl.created_at }}
            </p>
            <div class="d-flex gap-2">
              <button class="btn btn-sm btn-outline-primary" @click="applyTemplate(tpl.id)">套用</button>
              <button class="btn btn-sm btn-outline-danger" @click="deleteTemplate(tpl.id)">刪除</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const templates = ref([])

onMounted(async () => {
  const { data } = await axios.get('/api/templates')
  templates.value = data.templates || []
})

async function applyTemplate(id) {
  const { data } = await axios.post(`/api/templates/${id}/apply`)
  router.push(`/config/${data.session_id}`)
}

async function deleteTemplate(id) {
  await axios.delete(`/api/templates/${id}`)
  templates.value = templates.value.filter(t => t.id !== id)
}
</script>