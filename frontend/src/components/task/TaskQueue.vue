<template>
  <div class="task-queue">
    <div class="queue-header">
      <span class="queue-title">任务队列</span>
      <el-badge :value="runningCount" :max="99" type="primary" />
    </div>

    <div class="queue-list" v-if="queueTasks.length > 0">
      <div
        v-for="task in queueTasks"
        :key="task.id"
        class="queue-item"
        :class="{ 'is-running': task.status === 'running' }"
      >
        <div class="item-info">
          <span class="item-name">{{ task.name || '未命名任务' }}</span>
          <el-tag :type="getStatusType(task.status)" size="small">
            {{ getStatusText(task.status) }}
          </el-tag>
        </div>
        <div class="item-progress" v-if="task.status === 'running'">
          <el-progress
            :percentage="task.progress || 0"
            :stroke-width="4"
            :show-text="false"
          />
          <span class="progress-text">{{ task.progress || 0 }}%</span>
        </div>
      </div>
    </div>

    <el-empty v-else description="暂无任务" :image-size="60" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useTaskStore } from '@/store/task'
import { getStatusType, getStatusText } from '@/utils/format'

const taskStore = useTaskStore()

// 队列中的任务（运行中 + 等待中）
const queueTasks = computed(() => {
  return [...taskStore.runningTasks, ...taskStore.pendingTasks].slice(0, 5)
})

// 运行中的任务数量
const runningCount = computed(() => taskStore.runningTasks.length)
</script>

<style lang="scss" scoped>
.task-queue {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
}

.queue-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;

  .queue-title {
    font-weight: 600;
    color: #303133;
  }
}

.queue-list {
  .queue-item {
    padding: 12px;
    border-radius: 6px;
    background: #f5f7fa;
    margin-bottom: 8px;
    transition: background 0.3s;

    &:last-child {
      margin-bottom: 0;
    }

    &.is-running {
      background: #ecf5ff;
    }
  }

  .item-info {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;

    .item-name {
      font-size: 14px;
      color: #303133;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      max-width: 150px;
    }
  }

  .item-progress {
    display: flex;
    align-items: center;
    gap: 8px;

    .el-progress {
      flex: 1;
    }

    .progress-text {
      font-size: 12px;
      color: #909399;
      min-width: 36px;
    }
  }
}
</style>