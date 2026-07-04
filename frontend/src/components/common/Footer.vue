<template>
  <footer class="footer">
    <div class="footer-left">
      <span class="status-item">
        任务队列: <strong>{{ taskStore.tasks.length }}</strong>
      </span>
      <el-divider direction="vertical" />
      <span class="status-item" v-if="currentRunning">
        当前: <strong>{{ currentRunning.name }}</strong>
        ({{ currentRunning.progress || 0 }}%)
      </span>
    </div>

    <div class="footer-center">
      <span class="status-item">
        <el-icon :class="wsStatusClass"><Connection /></el-icon>
        WebSocket: {{ wsStatusText }}
      </span>
    </div>

    <div class="footer-right">
      <span>v1.0.0</span>
    </div>
  </footer>
</template>

<script setup>
import { computed, onMounted, onUnmounted } from 'vue'
import { useTaskStore } from '@/store/task'
import websocket from '@/utils/websocket'

const taskStore = useTaskStore()

// 当前运行的任务
const currentRunning = computed(() => {
  return taskStore.runningTasks[0] || null
})

// WebSocket状态
const wsConnected = computed(() => taskStore.wsConnected)

const wsStatusClass = computed(() => ({
  'ws-connected': wsConnected.value,
  'ws-disconnected': !wsConnected.value
}))

const wsStatusText = computed(() => {
  return wsConnected.value ? '已连接' : '未连接'
})

// WebSocket事件监听
const handleWsConnected = () => taskStore.setWsConnected(true)
const handleWsDisconnected = () => taskStore.setWsConnected(false)

onMounted(() => {
  websocket.on('connected', handleWsConnected)
  websocket.on('disconnected', handleWsDisconnected)
  // 初始化连接状态
  taskStore.setWsConnected(websocket.isConnected())
})

onUnmounted(() => {
  websocket.off('connected', handleWsConnected)
  websocket.off('disconnected', handleWsDisconnected)
})
</script>

<style lang="scss" scoped>
.footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 40px;
  padding: 0 24px;
  background: #fff;
  border-top: 1px solid #ebeef5;
  font-size: 13px;
  color: #909399;
}

.footer-left,
.footer-center,
.footer-right {
  display: flex;
  align-items: center;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 4px;

  strong {
    color: #303133;
  }
}

.ws-connected {
  color: #67c23a;
}

.ws-disconnected {
  color: #f56c6c;
}
</style>