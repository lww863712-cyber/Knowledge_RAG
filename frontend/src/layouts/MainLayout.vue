<template>
  <el-container class="layout">
    <el-aside width="220px">
      <div class="brand">one_RAG</div>
      <el-menu :default-active="$route.path" router class="menu">
        <el-menu-item index="/knowledge-bases">知识库管理</el-menu-item>
        <el-menu-item index="/documents">文档管理</el-menu-item>
        <el-menu-item index="/chat">对话问答</el-menu-item>
        <el-menu-item index="/retrieval">检索测试</el-menu-item>
        <el-menu-item index="/settings">系统设置</el-menu-item>
        <el-menu-item index="/usage">Token 用量</el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <div />
        <el-dropdown>
          <span class="user">{{ auth.username || '用户' }}</span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-header>
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.layout { height: 100vh; }
.brand { height: 56px; display: flex; align-items: center; padding: 0 20px; font-weight: 700; border-bottom: 1px solid #e5e7eb; }
.menu { border-right: none; }
.header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #e5e7eb; }
.user { cursor: pointer; }
.main { background: #f5f7fa; }
</style>