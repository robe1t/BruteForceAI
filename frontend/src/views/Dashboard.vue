<template>
  <div class="dashboard page-container">
    <div class="page-header">
      <h1 class="page-title">仪表盘</h1>
      <el-button type="primary" @click="$router.push('/task/create')">
        <el-icon><Plus /></el-icon>
        创建任务
      </el-button>
    </div>

    <!-- 统计卡片 -->
    <div class="stat-grid">
      <div class="stat-card stat-primary">
        <div class="stat-icon">📊</div>
        <div class="stat-value">{{ stats.total }}</div>
        <div class="stat-label">总任务数</div>
      </div>
      <div class="stat-card stat-info">
        <div class="stat-icon">🔄</div>
        <div class="stat-value">{{ stats.running }}</div>
        <div class="stat-label">运行中</div>
      </div>
      <div class="stat-card stat-success">
        <div class="stat-icon">✅</div>
        <div class="stat-value">{{ stats.completed }}</div>
        <div class="stat-label">已完成</div>
      </div>
      <div class="stat-card stat-warning">
        <div class="stat-icon">⚠️</div>
        <div class="stat-value">{{ stats.weakPwd }}</div>
        <div class="stat-label">发现弱口令</div>
      </div>
    </div>

    <!-- 内容区域 -->
    <el-row :gutter="20">
      <!-- 最近任务 -->
      <el-col :span="16">
        <div class="form-card">
          <div class="card-title">最近任务活动</div>
          <el-table :data="recentTasks" v-loading="loading" stripe>
            <el-table-column prop="name" label="任务名称" min-width="150">
              <template #default="{ row }">
                {{ row.name || '未命名任务' }}
              </template>
            </el-table-column>
            <el-table-column prop="target_url" label="目标URL" min-width="200">
              <template #default="{ row }">
                <el-tooltip :content="row.target_url" placement="top">
                  <span class="text-ellipsis">{{ truncateText(row.target_url, 30) }}</span>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)" size="small">
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="progress" label="进度" width="120">
              <template #default="{ row }">
                <el-progress
                  v-if="row.status === 'running'"
                  :percentage="row.progress || 0"
                  :stroke-width="6"
                />
                <span v-else>{{ row.progress || 0 }}%</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100" fixed="right">
              <template #default="{ row }">
                <el-button
                  type="primary"
                  text
                  size="small"
                  @click="handleViewTask(row)"
                >
                  查看
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-empty v-if="!loading && recentTasks.length === 0" description="暂无任务" />
        </div>
      </el-col>

      <!-- 安全评分分布 -->
      <el-col :span="8">
        <div class="form-card">
          <div class="card-title">安全评分分布</div>
          <ChartPanel
            type="pie"
            :data="scoreDistribution"
          />
        </div>
      </el-col>
    </el-row>

    <!-- 运行中的任务队列 -->
    <div class="form-card" v-if="runningTasks.length > 0">
      <div class="card-title">运行中的任务</div>
      <TaskQueue />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useTaskStore } from '@/store/task'
import { getOverviewStats } from '@/api/task'
import { getStatusType, getStatusText, truncateText } from '@/utils/format'
import ChartPanel from '@/components/report/ChartPanel.vue'
import TaskQueue from '@/components/task/TaskQueue.vue'

const router = useRouter()
const taskStore = useTaskStore()

const loading = ref(false)
const stats = ref({
  total: 0,
  running: 0,
  completed: 0,
  weakPwd: 0
})

// 最近任务列表
const recentTasks = computed(() => taskStore.tasks.slice(0, 5))

// 运行中的任务
const runningTasks = computed(() => taskStore.runningTasks)

// 评分分布数据
const scoreDistribution = computed(() => {
  const tasks = taskStore.completedTasks
  const high = tasks.filter(t => (t.score || 0) >= 80).length
  const medium = tasks.filter(t => (t.score || 0) >= 60 && (t.score || 0) < 80).length
  const low = tasks.filter(t => (t.score || 0) >= 40 && (t.score || 0) < 60).length
  const critical = tasks.filter(t => (t.score || 0) < 40).length

  return [
    { name: '安全', value: high },
    { name: '中等风险', value: medium },
    { name: '高风险', value: low },
    { name: '严重风险', value: critical }
  ].filter(item => item.value > 0)
})

// 查看任务详情
const handleViewTask = (task) => {
  if (task.status === 'completed') {
    router.push(`/report/${task.task_id}`)
  } else {
    router.push(`/task/${task.task_id}`)
  }
}

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    // 并行请求
    const [statsData] = await Promise.all([
      getOverviewStats(),
      taskStore.fetchTasks({ limit: 10 })
    ])

    if (statsData) {
      stats.value = {
        total: statsData.total || 0,
        running: statsData.running || 0,
        completed: statsData.completed || 0,
        weakPwd: statsData.weak_credentials || 0
      }
    }
  } catch (error) {
    console.error('加载数据失败:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<style lang="scss" scoped>
.dashboard {
  .text-ellipsis {
    display: inline-block;
    max-width: 200px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}
</style>