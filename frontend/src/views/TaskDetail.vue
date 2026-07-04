<template>
  <div class="task-detail page-container" v-loading="loading">
    <div class="page-header">
      <div class="header-left">
        <el-button text @click="$router.back()">
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <h1 class="page-title">任务详情: {{ task?.name || '未命名任务' }}</h1>
      </div>
      <div class="header-actions">
        <el-button
          v-if="task?.status === 'running'"
          type="danger"
          @click="handleStop"
          :loading="actionLoading"
        >
          停止任务
        </el-button>
        <el-button
          v-if="task?.status === 'completed'"
          type="success"
          @click="$router.push(`/report/${task.task_id}`)"
        >
          查看报告
        </el-button>
      </div>
    </div>

    <!-- 任务基本信息 -->
    <div class="form-card" v-if="task">
      <el-descriptions :column="4" border>
        <el-descriptions-item label="目标URL">
          <el-link :href="task.target_url" target="_blank" type="primary">
            {{ task.target_url }}
          </el-link>
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(task.status)">
            {{ getStatusText(task.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="开始时间">
          {{ formatDateTime(task.started_at) || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="运行时间">
          {{ formatDuration(task.elapsed_time) }}
        </el-descriptions-item>
      </el-descriptions>

      <!-- 进度条 -->
      <div class="progress-section" v-if="task.status === 'running'">
        <div class="progress-label">
          进度: {{ task.current_index || 0 }} / {{ task.total_count || 0 }} ({{ task.progress || 0 }}%)
        </div>
        <el-progress
          :percentage="task.progress || 0"
          :stroke-width="10"
          :show-text="true"
          striped
          striped-flow
        />
      </div>
    </div>

    <!-- 实时日志 - 全宽显示 -->
    <div class="form-card" v-if="task">
      <div class="card-title">
        <span>实时日志</span>
        <el-button text size="small" @click="clearLogs">清空</el-button>
      </div>
      <div class="log-container scroll-container" ref="logContainerRef">
        <div
          v-for="(log, index) in logs"
          :key="index"
          class="log-item"
          :class="`log-${log.level}`"
        >
          <span class="log-time">[{{ log.time }}]</span>
          <span class="log-message">{{ log.message }}</span>
        </div>
        <el-empty v-if="logs.length === 0" description="暂无日志" :image-size="60" />
      </div>
    </div>

    <!-- 统计信息 -->
    <div class="form-card" v-if="task">
      <div class="card-title">统计信息</div>
      <el-row :gutter="20">
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-value text-success">{{ task.success_count || 0 }}</div>
            <div class="stat-label">成功发现</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-value text-danger">{{ task.failed_count || 0 }}</div>
            <div class="stat-label">失败次数</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-value">{{ task.total_requests || task.current_index || 0 }}</div>
            <div class="stat-label">总请求数</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-value">{{ task.avg_response_time || 0 }}ms</div>
            <div class="stat-label">平均响应</div>
          </div>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getTaskDetail, stopTask, getTaskLogs, getTaskProgress } from '@/api/task'
import { getStatusType, getStatusText, formatDateTime, formatDuration } from '@/utils/format'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const actionLoading = ref(false)
const task = ref(null)
const logContainerRef = ref(null)
const logs = ref([])
const pollInterval = ref(null)
const progressInterval = ref(null)

// 获取任务ID
const taskId = computed(() => route.params.id)

// 获取任务详情
const fetchTaskDetail = async () => {
  loading.value = true
  try {
    task.value = await getTaskDetail(taskId.value)
    // 如果任务正在运行，启动定时轮询
    if (task.value.status === 'running' || task.value.status === 'pending') {
      startPolling()
    }
    // 获取初始日志
    await fetchLogs()
  } catch (error) {
    console.error('获取任务详情失败:', error)
    ElMessage.error('获取任务详情失败')
    router.back()
  } finally {
    loading.value = false
  }
}

// 获取日志 - 每2秒轮询
const fetchLogs = async () => {
  try {
    const result = await getTaskLogs(taskId.value, { limit: 200 })
    if (result.logs && result.logs.length > 0) {
      // 转换日志格式
      logs.value = result.logs.map(log => ({
        level: log.level || 'info',
        time: formatTime(log.timestamp || log.created_at),
        message: log.message
      }))
    }
  } catch (error) {
    console.error('获取日志失败:', error)
  }
}

// 获取进度 - 每2秒轮询
const fetchProgress = async () => {
  try {
    const result = await getTaskProgress(taskId.value)
    if (result && task.value) {
      task.value.status = result.status
      task.value.current_index = result.current
      task.value.total_count = result.total
      task.value.progress = result.progress
      task.value.success_count = result.success_count
    }
    // 如果任务完成，停止轮询
    if (result.status === 'completed' || result.status === 'stopped' || result.status === 'failed') {
      stopPolling()
      // 获取最终详情
      task.value = await getTaskDetail(taskId.value)
    }
  } catch (error) {
    console.error('获取进度失败:', error)
  }
}

// 启动定时轮询
const startPolling = () => {
  if (pollInterval.value) return

  // 每2秒获取日志
  pollInterval.value = setInterval(async () => {
    await fetchLogs()
    await fetchProgress()
  }, 2000)
}

// 停止定时轮询
const stopPolling = () => {
  if (pollInterval.value) {
    clearInterval(pollInterval.value)
    pollInterval.value = null
  }
}

// 格式化时间（加8小时转北京时间）
const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  // 加8小时
  const beijingDate = new Date(date.getTime() + 8 * 60 * 60 * 1000)
  return beijingDate.toLocaleTimeString('zh-CN', { hour12: false })
}

// 停止任务
const handleStop = async () => {
  actionLoading.value = true
  try {
    await stopTask(taskId.value)
    ElMessage.success('任务已停止')
    stopPolling()
    task.value.status = 'stopped'
  } catch (error) {
    console.error('停止失败:', error)
  } finally {
    actionLoading.value = false
  }
}

// 清空日志
const clearLogs = () => {
  logs.value = []
}

// 自动滚动到最新日志
watch(() => logs.value.length, async () => {
  await nextTick()
  if (logContainerRef.value) {
    logContainerRef.value.scrollTop = logContainerRef.value.scrollHeight
  }
})

onMounted(() => {
  fetchTaskDetail()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style lang="scss" scoped>
.task-detail {
  .header-left {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .progress-section {
    margin-top: 20px;

    .progress-label {
      margin-bottom: 8px;
      font-size: 14px;
      color: #606266;
    }
  }

  .log-container {
    max-height: 500px;
    min-height: 300px;
  }

  .stat-item {
    text-align: center;
    padding: 16px;

    .stat-value {
      font-size: 28px;
      font-weight: 700;
      color: #303133;

      &.text-success {
        color: #67c23a;
      }

      &.text-danger {
        color: #f56c6c;
      }
    }

    .stat-label {
      font-size: 14px;
      color: #909399;
      margin-top: 4px;
    }
  }
}
</style>