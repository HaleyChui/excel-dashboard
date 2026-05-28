import { createRouter, createWebHistory } from 'vue-router'
import UploadView from '../views/UploadView.vue'

const routes = [
  { path: '/', name: 'upload', component: UploadView },
  { path: '/config/:sessionId', name: 'config', component: () => import('../views/ConfigView.vue') },
  { path: '/dashboard/:sessionId', name: 'dashboard', component: () => import('../views/DashboardView.vue') },
  { path: '/dashboard/:sessionId/:version', name: 'dashboard-version', component: () => import('../views/DashboardView.vue') },
  { path: '/templates', name: 'templates', component: () => import('../views/TemplatesView.vue') },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})