import { defineStore } from 'pinia'
import { ref } from 'vue'

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

interface ChatCache {
  kbId: number | null
  messages: ChatMessage[]
  citations: any[]
}

const STORAGE_KEY = 'one_rag_chat'

function loadCache(): ChatCache {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) return JSON.parse(raw)
  } catch {
    // ignore corrupted cache
  }
  return { kbId: null, messages: [], citations: [] }
}

export const useChatStore = defineStore('chat', () => {
  const cache = loadCache()
  const kbId = ref<number | null>(cache.kbId)
  const messages = ref<ChatMessage[]>(cache.messages || [])
  const citations = ref<any[]>(cache.citations || [])

  function persist() {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ kbId: kbId.value, messages: messages.value, citations: citations.value })
    )
  }

  function setKnowledgeBaseId(id: number | null) {
    if (id !== kbId.value) {
      messages.value = []
      citations.value = []
    }
    kbId.value = id
    persist()
  }

  function pushMessage(role: 'user' | 'assistant', content: string) {
    messages.value.push({ role, content })
    persist()
  }

  function appendToLast(content: string) {
    if (messages.value.length) {
      messages.value[messages.value.length - 1].content += content
      persist()
    }
  }

  function setLastMessage(content: string) {
    if (messages.value.length) {
      messages.value[messages.value.length - 1].content = content
      persist()
    }
  }

  function setCitations(items: any[]) {
    citations.value = items
    persist()
  }

  function clear() {
    messages.value = []
    citations.value = []
    persist()
  }

  return {
    kbId,
    messages,
    citations,
    setKnowledgeBaseId,
    pushMessage,
    appendToLast,
    setLastMessage,
    setCitations,
    clear,
    persist
  }
})