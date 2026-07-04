<template>
  <header class="navbar">
    <div class="navbar-left">
      <router-link to="/" class="logo">
        <el-icon :size="24"><Monitor /></el-icon>
        <span class="logo-text">智能爆破安全审计系统</span>
      </router-link>
    </div>

    <nav class="navbar-center">
      <router-link
        v-for="item in menuItems"
        :key="item.path"
        :to="item.path"
        class="nav-item"
        :class="{ active: isActive(item.path) }"
      >
        <el-icon><component :is="item.icon" /></el-icon>
        <span>{{ item.title }}</span>
      </router-link>
    </nav>

    <div class="navbar-right">
      <el-badge :value="runningCount" :hidden="runningCount === 0" class="badge-item">
        <el-button text @click="$router.push('/task/list')">
          <el-icon><Bell /></el-icon>
        </el-button>
      </el-badge>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useTaskStore } from '@/store/task'

const route = useRoute()
const taskStore = useTaskStore()

// 菜单项
const menuItems = [
  { path: '/', title: '仪表盘', icon: 'DataBoard' },
  { path: '/task/list', title: '任务', icon: 'List' },
  { path: '/config', title: '配置', icon: 'Setting' },
  { path: '/dictionary', title: '字典', icon: 'Document' }
]

// 运行中的任务数量
const runningCount = computed(() => taskStore.runningTasks.length)

// 判断菜单是否激活
const isActive = (path) => {
  if (path === '/') {
    return route.path === '/'
  }
  return route.path.startsWith(path)
}
</script>

<style lang="scss" scoped>
.navbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 60px;
  padding: 0 24px;
  background: #fff;
  border-bottom: 1px solid #ebeef5;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}

.navbar-left {
  .logo {
    display: flex;
    align-items: center;
    gap: 8px;
    text-decoration: none;
    color: #409eff;

    .logo-text {
      font-size: 18px;
      font-weight: 600;
    }
  }
}

.navbar-center {
  display: flex;
  align-items: center;
  gap: 8px;

  .nav-item {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 8px 16px;
    border-radius: 8px;
    text-decoration: none;
    color: #606266;
    transition: all 0.3s;

    &:hover {
      background: #f5f7fa;
      color: #409eff;
    }

    &.active {
      background: #ecf5ff;
      color: #409eff;
      font-weight: 500;
    }
  }
}

.navbar-right {
  display: flex;
  align-items: center;

  .badge-item {
    margin-right: 8px;
  }
}
</style>