import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { title: '仪表盘' }
  },
  {
    path: '/task/create',
    name: 'TaskCreate',
    component: () => import('@/views/TaskCreate.vue'),
    meta: { title: '创建任务' }
  },
  {
    path: '/task/list',
    name: 'TaskList',
    component: () => import('@/views/TaskList.vue'),
    meta: { title: '任务列表' }
  },
  {
    path: '/task/:id',
    name: 'TaskDetail',
    component: () => import('@/views/TaskDetail.vue'),
    meta: { title: '任务详情' }
  },
  {
    path: '/report/:id',
    name: 'Report',
    component: () => import('@/views/Report.vue'),
    meta: { title: '安全报告' }
  },
  {
    path: '/config',
    name: 'Config',
    component: () => import('@/views/Config.vue'),
    meta: { title: '系统配置' }
  },
  {
    path: '/dictionary',
    name: 'Dictionary',
    component: () => import('@/views/Dictionary.vue'),
    meta: { title: '字典管理' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫 - 设置页面标题
router.beforeEach((to, from, next) => {
  document.title = `${to.meta.title} - 智能爆破安全审计系统`
  next()
})

export default router