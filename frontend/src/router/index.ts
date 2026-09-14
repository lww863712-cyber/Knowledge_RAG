import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'login', component: () => import('@/views/LoginView.vue') },
    {
      path: '/',
      component: () => import('@/layouts/MainLayout.vue'),
      redirect: '/knowledge-bases',
      children: [
        { path: 'knowledge-bases', name: 'knowledge-bases', component: () => import('@/views/KnowledgeBasesView.vue') },
        { path: 'documents', name: 'documents', component: () => import('@/views/DocumentsView.vue') },
        { path: 'chat', name: 'chat', component: () => import('@/views/ChatView.vue') },
        { path: 'retrieval', name: 'retrieval', component: () => import('@/views/RetrievalView.vue') },
        { path: 'settings', name: 'settings', component: () => import('@/views/SettingsView.vue') },
        { path: 'usage', name: 'usage', component: () => import('@/views/UsageView.vue') }
      ]
    }
  ]
})

router.beforeEach((to) => {
  const token = localStorage.getItem('token')
  if (to.path !== '/login' && !token) {
    return '/login'
  }
  if (to.path === '/login' && token) {
    return '/knowledge-bases'
  }
  return true
})

export default router