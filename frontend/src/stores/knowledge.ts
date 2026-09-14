import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useKnowledgeStore = defineStore('knowledge', () => {
  const currentKbId = ref<number | null>(Number(localStorage.getItem('kbId') || 0) || null)

  function setCurrentKbId(id: number | null) {
    currentKbId.value = id
    if (id) {
      localStorage.setItem('kbId', String(id))
    } else {
      localStorage.removeItem('kbId')
    }
  }

  return { currentKbId, setCurrentKbId }
})