<template>
  <el-card>
    <div class="toolbar">
      <h3>知识库管理</h3>
      <el-button type="primary" @click="dialogVisible = true">新建知识库</el-button>
    </div>

    <el-table :data="items" v-loading="loading">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="description" label="描述" />
      <el-table-column label="操作" width="180">
        <template #default="{ row }">
          <el-button size="small" @click="select(row)">选择</el-button>
          <el-popconfirm title="确认删除该知识库？" @confirm="remove(row.id)">
            <template #reference>
              <el-button size="small" type="danger">删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" title="新建知识库" width="420px">
      <el-form label-width="70px">
        <el-form-item label="名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="create">创建</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api/http'
import { useKnowledgeStore } from '@/stores/knowledge'

interface KnowledgeBase { id: number; name: string; description?: string }

const store = useKnowledgeStore()
const items = ref<KnowledgeBase[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const form = reactive({ name: '', description: '' })

async function load() {
  loading.value = true
  try {
    const { data } = await api.get('/api/v1/knowledge-bases')
    items.value = data
  } finally {
    loading.value = false
  }
}

async function create() {
  try {
    await api.post('/api/v1/knowledge-bases', form)
    ElMessage.success('创建成功')
    dialogVisible.value = false
    form.name = ''
    form.description = ''
    load()
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || err.message || '创建失败')
  }
}

async function remove(id: number) {
  try {
    await api.delete(`/api/v1/knowledge-bases/${id}`)
    ElMessage.success('已删除')
    if (store.currentKbId === id) store.setCurrentKbId(null)
    load()
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || err.message || '删除失败')
  }
}

function select(row: KnowledgeBase) {
  store.setCurrentKbId(row.id)
  ElMessage.success(`已选择：${row.name}`)
}

onMounted(load)
</script>

<style scoped>
.toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
</style>