<template>
  <el-card class="chat-card">
    <div class="toolbar">
      <h3>对话问答</h3>
      <el-select v-model="kbId" placeholder="选择知识库" style="width: 220px" @change="onKbChange">
        <el-option v-for="kb in kbs" :key="kb.id" :label="kb.name" :value="kb.id" />
      </el-select>
    </div>

    <div class="messages">
      <div v-for="(item, index) in chat.messages" :key="index" :class="['message', item.role]">
        <div class="bubble">{{ item.content }}</div>
      </div>
      <div v-if="sending" class="message assistant">
        <div class="bubble running">正在生成回答，请稍候...</div>
      </div>
      <div v-if="chat.citations.length" class="citations">
        <h4>引用来源</h4>
        <div v-for="(cite, index) in chat.citations" :key="index" class="citation">
          <strong>[{{ index + 1 }}]</strong> {{ cite.metadata?.document_name || cite.metadata?.filename || '未知来源' }}
        </div>
      </div>
    </div>

    <div class="input-row">
      <el-input v-model="input" placeholder="输入问题，例如：检索并总结这些资料" :disabled="sending" @keyup.enter="send" />
      <el-button type="primary" :loading="sending" @click="send">发送</el-button>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api/http'
import { useKnowledgeStore } from '@/stores/knowledge'
import { useChatStore } from '@/stores/chat'

interface KnowledgeBase { id: number; name: string }

const store = useKnowledgeStore()
const chat = useChatStore()
const kbs = ref<KnowledgeBase[]>([])
const kbId = ref<number | null>(store.currentKbId ?? chat.kbId)
const input = ref('')
const sending = ref(false)

async function loadKbs() {
  const { data } = await api.get('/api/v1/knowledge-bases')
  kbs.value = data
  if (!kbId.value && data.length) {
    const preferred = chat.kbId && data.some((kb: KnowledgeBase) => kb.id === chat.kbId)
      ? chat.kbId
      : data[0].id
    kbId.value = preferred
    store.setCurrentKbId(preferred)
  }
  chat.setKnowledgeBaseId(kbId.value)
}

function onKbChange() {
  if (kbId.value) store.setCurrentKbId(kbId.value)
  chat.setKnowledgeBaseId(kbId.value)
}

async function send() {
  if (!input.value.trim() || !kbId.value || sending.value) return
  const question = input.value.trim()
  input.value = ''
  chat.pushMessage('user', question)
  chat.pushMessage('assistant', '')
  chat.setCitations([])
  sending.value = true

  try {
    const token = localStorage.getItem('token')
    const response = await fetch('/api/v1/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({
        knowledge_base_id: kbId.value,
        message: question,
        history: chat.messages.slice(0, -1).map((m) => ({ role: m.role, content: m.content }))
      })
    })
    if (!response.body) throw new Error('不支持流式响应')
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n\n')
      buffer = lines.pop() || ''
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const payload = JSON.parse(line.slice(6))
        if (payload.type === 'token') {
          chat.appendToLast(payload.content)
        } else if (payload.type === 'citations') {
          chat.setCitations(payload.content)
        }
      }
    }
    if (!chat.messages[chat.messages.length - 1].content.trim()) {
      chat.setLastMessage('未返回内容。')
    }
  } catch (err: any) {
    chat.setLastMessage(`请求失败：${err.message || err}`)
    ElMessage.error('对话请求失败')
  } finally {
    sending.value = false
  }
}

onMounted(loadKbs)
</script>

<style scoped>
.chat-card { height: calc(100vh - 90px); display: flex; flex-direction: column; }
.toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.messages { flex: 1; overflow-y: auto; padding: 12px; background: #fff; border: 1px solid #e5e7eb; border-radius: 6px; }
.message { margin-bottom: 14px; display: flex; }
.message.user { justify-content: flex-end; }
.message.assistant { justify-content: flex-start; }
.bubble { max-width: 78%; padding: 10px 14px; border-radius: 10px; white-space: pre-wrap; }
.user .bubble { background: #409eff; color: #fff; }
.assistant .bubble { background: #f0f2f5; color: #303133; }
.assistant .bubble.running { color: #409eff; }
.citations { margin-top: 16px; padding: 10px; background: #fafafa; border-radius: 6px; }
.citation { margin-bottom: 6px; }
.input-row { display: flex; gap: 10px; margin-top: 12px; }
</style>