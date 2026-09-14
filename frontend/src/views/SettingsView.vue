<template>
  <el-card>
    <h3>系统设置</h3>
    <el-descriptions :column="2" border>
      <el-descriptions-item label="LLM Provider">{{ settings.llm_provider || '-' }}</el-descriptions-item>
      <el-descriptions-item label="LLM Model">{{ settings.llm_model || '使用 provider 默认值' }}</el-descriptions-item>
      <el-descriptions-item label="LLM Base URL">{{ settings.llm_base_url || '使用 provider 默认值' }}</el-descriptions-item>
      <el-descriptions-item label="Temperature">{{ settings.llm_temperature ?? '-' }}</el-descriptions-item>
      <el-descriptions-item label="Embedding Provider">{{ settings.embedding_provider || '-' }}</el-descriptions-item>
      <el-descriptions-item label="Embedding Model">{{ settings.embedding_model || '-' }}</el-descriptions-item>
      <el-descriptions-item label="Reranker Model">{{ settings.reranker_model || '-' }}</el-descriptions-item>
    </el-descriptions>

    <el-divider content-position="left">配置模型单价</el-divider>
    <el-form :model="priceForm" label-width="120px" class="price-form">
      <el-form-item label="Provider">
        <el-input v-model="priceForm.provider" placeholder="deepseek" />
      </el-form-item>
      <el-form-item label="模型名">
        <el-input v-model="priceForm.model_name" placeholder="deepseek-chat" />
      </el-form-item>
      <el-form-item label="输入单价/百万">
        <el-input-number v-model="priceForm.unit_price_input" :min="0" />
      </el-form-item>
      <el-form-item label="输出单价/百万">
        <el-input-number v-model="priceForm.unit_price_output" :min="0" />
      </el-form-item>
      <el-button type="primary" @click="savePrice">保存配置</el-button>
    </el-form>
  </el-card>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api/http'

interface Settings { llm_provider?: string; llm_model?: string; llm_base_url?: string; llm_temperature?: number; embedding_provider?: string; embedding_model?: string; reranker_model?: string }

const settings = ref<Settings>({})
const priceForm = reactive({
  provider: '',
  model_name: '',
  base_url: '',
  api_key_ref: '',
  unit_price_input: 0,
  unit_price_output: 0,
  is_active: true
})

async function load() {
  const { data } = await api.get('/api/v1/settings/models')
  settings.value = data
}

async function savePrice() {
  await api.post('/api/v1/settings/models', priceForm)
  ElMessage.success('已保存')
  load()
}

onMounted(load)
</script>

<style scoped>
.price-form { max-width: 520px; margin-top: 16px; }
</style>