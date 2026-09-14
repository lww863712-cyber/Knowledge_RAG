<template>
  <el-card>
    <div class="toolbar">
      <h3>检索测试</h3>
      <el-select v-model="kbId" placeholder="选择知识库" style="width: 220px" @change="loadKbs">
        <el-option v-for="kb in kbs" :key="kb.id" :label="kb.name" :value="kb.id" />
      </el-select>
    </div>

    <el-space>
      <el-input v-model="query" placeholder="输入检索词" style="width: 420px" @keyup.enter="search" />
      <el-input-number v-model="topK" :min="1" :max="50" />
      <el-button type="primary" :loading="loading" @click="search">检索</el-button>
    </el-space>

    <el-table :data="results" class="table" v-loading="loading">
      <el-table-column type="index" label="#" width="60" />
      <el-table-column prop="score" label="重排分数" width="110" />
      <el-table-column prop="content" label="内容" />
      <el-table-column label="来源" width="220">
        <template #default="{ row }">{{ row.metadata?.document_name || row.metadata?.filename }}</template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api/http'
import { useKnowledgeStore } from '@/stores/knowledge'

interface KnowledgeBase { id: number; name: string }
interface Result { score: number; content: string; metadata: Record<string, any> }

const store = useKnowledgeStore()
const kbs = ref<KnowledgeBase[]>([])
const kbId = ref<number | null>(store.currentKbId)
const query = ref('')
const topK = ref(6)
const results = ref<Result[]>([])
const loading = ref(false)

async function loadKbs() {
  const { data } = await api.get('/api/v1/knowledge-bases')
  kbs.value = data
  if (!kbId.value && data.length) {
    kbId.value = data[0].id
    store.setCurrentKbId(kbId.value)
  }
}

async function search() {
  if (!kbId.value || !query.value.trim()) return
  loading.value = true
  try {
    const { data } = await api.post('/api/v1/retrieval/search', {
      knowledge_base_id: kbId.value,
      query: query.value.trim(),
      top_k: topK.value
    })
    results.value = data.results
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '检索失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadKbs)
</script>

<style scoped>
.toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.table { margin-top: 16px; }
</style>