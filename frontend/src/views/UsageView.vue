<template>
  <el-card>
    <div class="toolbar">
      <h3>Token 用量</h3>
      <el-select v-model="days" @change="load">
        <el-option label="近 7 天" :value="7" />
        <el-option label="近 30 天" :value="30" />
        <el-option label="近 90 天" :value="90" />
      </el-select>
    </div>

    <el-row :gutter="16">
      <el-col :span="8"><el-card><div class="metric">输入 Token</div><div class="value">{{ summary.total_input_tokens }}</div></el-card></el-col>
      <el-col :span="8"><el-card><div class="metric">输出 Token</div><div class="value">{{ summary.total_output_tokens }}</div></el-card></el-col>
      <el-col :span="8"><el-card><div class="metric">估算费用</div><div class="value">¥{{ summary.total_cost }}</div></el-card></el-col>
    </el-row>

    <h4>按 Provider / 模型</h4>
    <el-table :data="summary.by_provider" size="small">
      <el-table-column prop="provider" label="Provider" />
      <el-table-column prop="model" label="模型" />
      <el-table-column prop="input_tokens" label="输入" />
      <el-table-column prop="output_tokens" label="输出" />
      <el-table-column prop="cost" label="费用" />
    </el-table>

    <h4>按日期</h4>
    <el-table :data="summary.by_day" size="small">
      <el-table-column prop="date" label="日期" />
      <el-table-column prop="input_tokens" label="输入" />
      <el-table-column prop="output_tokens" label="输出" />
      <el-table-column prop="cost" label="费用" />
    </el-table>
  </el-card>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import api from '@/api/http'

interface Summary { total_input_tokens: number; total_output_tokens: number; total_cost: number; by_provider: any[]; by_day: any[] }

const days = ref(30)
const summary = reactive<Summary>({ total_input_tokens: 0, total_output_tokens: 0, total_cost: 0, by_provider: [], by_day: [] })

async function load() {
  const { data } = await api.get('/api/v1/usage/summary', { params: { days: days.value } })
  Object.assign(summary, data)
}

onMounted(load)
</script>

<style scoped>
.toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.metric { color: #909399; margin-bottom: 8px; }
.value { font-size: 26px; font-weight: 700; }
</style>