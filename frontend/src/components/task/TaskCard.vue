<template>
  <el-card class="task-card" :body-style="{ padding: '16px' }" shadow="hover">
    <div class="task-header">
      <div class="task-title">
        <el-icon><Document /></el-icon>
        <span>{{ task.name || '未命名任务' }}</span>
      </div>
      <el-tag :type="getStatusType(task.status)" size="small">
        {{ getStatusText(task.status) }}
      </el-tag>
    </div>

    <div class="task-info">
      <div class="info-item">
        <el-icon><Link /></el-icon>
        <span class="info-label">目标:</span>
        <span class="info-value" :title="task.target_url">
          {{ truncateText(task.target_url, 40) }}
        </span>
      </div>
      <div class="info-item">
        <el-icon><Clock /></el-icon>
        <span class="info-label">创建:</span>
        <span class="info-value">{{ formatDateTime(task.created_at) }}</span>
      </div>
    </div>

    <!-- 进度条 -->
    <div class="task-progress" v-if="task.status === 'running'">
      <el-progress
        :percentage="task.progress || 0"
        :stroke-width="6"
        :show-text="true"
      />
    </div>

    <!-- 操作按钮 -->
    <div class="task-actions">
      <el-button
        v-if="task.status === 'pending'"
        type="primary"
        size="small"
        @click="handleStart"
        :loading="loading"
      >
        启动
      </el-button>
      <el-button
        v-if="task.status === 'running'"
        type="danger"
        size="small"
        @click="handleStop"
        :loading="loading"
      >
        停止
      </el-button>
      <el-button
        v-if="task.status === 'stopped'"
        type="primary"
        size="small"
        @click="handleStart"
        :loading="loading"
      >
        继续
      </el-button>
      <el-button
        v-if="task.status === 'completed'"
        type="success"
        size="small"
        @click="handleViewReport"
      >
        查看报告
      </el-button>
      <el-button size="small" @click="handleViewDetail">
        详情
      </el-button>
      <el-button
        v-if="['completed', 'failed', 'stopped'].includes(task.status)"
        type="danger"
        size="small"
        text
        @click="handleDelete"
        :loading="loading"
      >
        删除
      </el-button>
    </div>
  </el-card>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { startTask, stopTask, deleteTask } from '@/api/task'
import { getStatusType, getStatusText, truncateText, formatDateTime } from '@/utils/format'

const props = defineProps({
  task: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['refresh'])
const router = useRouter()
const loading = ref(false)

// 启动任务
const handleStart = async () => {
  loading.value = true
  try {
    await startTask(props.task.id)
    ElMessage.success('任务已启动')
    emit('refresh')
  } catch (error) {
    console.error('启动失败:', error)
  } finally {
    loading.value = false
  }
}

// 停止任务
const handleStop = async () => {
  loading.value = true
  try {
    await stopTask(props.task.id)
    ElMessage.success('任务已停止')
    emit('refresh')
  } catch (error) {
    console.error('停止失败:', error)
  } finally {
    loading.value = false
  }
}

// 删除任务
const handleDelete = async () => {
  try {
    await ElMessageBox.confirm('确定要删除此任务吗?', '提示', {
      type: 'warning'
    })

    loading.value = true
    await deleteTask(props.task.id)
    ElMessage.success('任务已删除')
    emit('refresh')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
    }
  } finally {
    loading.value = false
  }
}

// 查看详情
const handleViewDetail = () => {
  router.push(`/task/${props.task.id}`)
}

// 查看报告
const handleViewReport = () => {
  router.push(`/report/${props.task.id}`)
}
</script>

<style lang="scss" scoped>
.task-card {
  margin-bottom: 16px;
  transition: transform 0.2s;

  &:hover {
    transform: translateY(-2px);
  }
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;

  .task-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
    color: #303133;
  }
}

.task-info {
  margin-bottom: 12px;

  .info-item {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 13px;
    color: #606266;
    margin-bottom: 4px;

    .info-label {
      color: #909399;
    }

    .info-value {
      color: #303133;
    }
  }
}

.task-progress {
  margin-bottom: 12px;
}

.task-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>