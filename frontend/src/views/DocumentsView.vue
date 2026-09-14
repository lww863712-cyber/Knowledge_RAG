<template>
  <el-card>
    <div class="toolbar">
      <h3>文档管理</h3>
      <el-select v-model="kbId" placeholder="选择知识库" style="width: 220px" @change="load">
        <el-option v-for="kb in kbs" :key="kb.id" :label="kb.name" :value="kb.id" />
      </el-select>
    </div>

    <el-space wrap>
      <el-upload :show-file-list="false" :http-request="upload">
        <el-button type="primary" :disabled="!kbId">上传文件</el-button>
      </el-upload>
      <el-input v-model="scanPath" placeholder="容器内目录路径" style="width: 320px" />
      <el-button :disabled="!kbId" @click="scan">扫描目录</el-button>
      <el-input v-model="url" placeholder="网页 URL" style="width: 320px" />
      <el-button :disabled="!kbId" @click="importUrl">导入 URL</el-button>
    </el-space>

    <el-table :data="documents" v-loading="loading" class="table">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="name" label="文件名" />
      <el-table-column prop="file_type" label="类型" width="90" />
      <el-table-column prop="status" label="状态" width="110" />
      <el-table-column prop="source" label="来源" width="100" />
      <el-table-column label="操作" width="180">
        <template #default="{ row }">
          <el-button size="small" @click="reindex(row.id)">重建索引</el-button>
          <el-popconfirm title="确认删除该文档？" @confirm="remove(row.id)">
            <template #reference>
              <el-button size="small" type="danger">删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <h4>导入任务</h4>
    <el-table :data="jobs" size="small">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="job_type" label="类型" width="100" />
      <el-table-column prop="status" label="状态" width="110" />
      <el-table-column prop="progress" label="进度" width="100" />
      <el-table-column prop="error_message" label="错误信息" />
    </el-table>
  </el-card>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api/http'
import { useKnowledgeStore } from '@/stores/knowledge'

interface KnowledgeBase { id: number; name: string }
interface DocumentItem { id: number; name: string; file_type: string; status: string; source: string }
interface Job { id: number; job_type: string; status: string; progress: number; error_message?: string }

const store = useKnowledgeStore()
const kbs = ref<KnowledgeBase[]>([])
const kbId = ref<number | null>(store.currentKbId)
const documents = ref<DocumentItem[]>([])
const jobs = ref<Job[]>([])
const loading = ref(false)
const scanPath = ref('/data/files')
const url = ref('')

async function loadKbs() {
  const { data } = await api.get('/api/v1/knowledge-bases')
  kbs.value = data
  if (!kbId.value && data.length) {
    kbId.value = data[0].id
    store.setCurrentKbId(kbId.value)
  }
  if (kbId.value) load()
}

async function load() {
  if (!kbId.value) return
  loading.value = true
  try {
    const [docRes, jobRes] = await Promise.all([
      api.get('/api/v1/documents', { params: { knowledge_base_id: kbId.value } }),
      api.get('/api/v1/ingestion/jobs', { params: { knowledge_base_id: kbId.value } })
    ])
    documents.value = docRes.data
    jobs.value = jobRes.data
  } finally {
    loading.value = false
  }
}

async function upload(options: any) {
  if (!kbId.value) return
  const form = new FormData()
  form.append('file', options.file)
  form.append('knowledge_base_id', String(kbId.value))
  await api.post('/api/v1/ingestion/upload', form)
  ElMessage.success('上传任务已提交')
  load()
}

async function scan() {
  if (!kbId.value) return
  await api.post('/api/v1/ingestion/scan', { knowledge_base_id: kbId.value, directory: scanPath.value })
  ElMessage.success('扫描任务已提交')
  load()
}

async function importUrl() {
  if (!kbId.value) return
  await api.post('/api/v1/ingestion/url', { knowledge_base_id: kbId.value, url: url.value })
  ElMessage.success('URL 导入任务已提交')
  url.value = ''
  load()
}

async function reindex(id: number) {
  await api.post(`/api/v1/documents/${id}/reindex`)
  ElMessage.success('重建索引已触发')
  load()
}

async function remove(id: number) {
  await api.delete(`/api/v1/documents/${id}`)
  ElMessage.success('已删除')
  load()
}

onMounted(loadKbs)
</script>

<style scoped>
.toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.table { margin-top: 16px; margin-bottom: 24px; }
</style>