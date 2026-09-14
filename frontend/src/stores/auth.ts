import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api/http'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const username = ref(localStorage.getItem('username') || '')

  async function login(name: string, password: string) {
    const { data } = await api.post('/api/v1/auth/login', { username: name, password })
    token.value = data.access_token
    username.value = name
    localStorage.setItem('token', token.value)
    localStorage.setItem('username', name)
    api.defaults.headers.common.Authorization = `Bearer ${token.value}`
  }

  function logout() {
    token.value = ''
    username.value = ''
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    delete api.defaults.headers.common.Authorization
  }

  return { token, username, login, logout }
})