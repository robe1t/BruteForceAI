<template>
  <div class="task-list page-container">
    <div class="page-header">
      <h1 class="page-title">任务列表</h1>
      <el-button type="primary" @click="$router.push('/task/create')">
        <el-icon><Plus /></el-icon>
        创建任务
      </el-button>
    </div>

    <!-- 筛选条件 -->
    <div class="filter-bar">
      <el-select v-model="filterStatus" placeholder="状态筛选" clearable @change="handleFilter">
        <el-option label="全部" value="" />
        <el-option label="等待中" value="pending" />
        <el-option label="运行中" value="running" />
        <el-option label="已完成" value="completed" />
        <el-option label="已停止" value="stopped" />
        <el-option label="失败" value="failed" />
      </el-select>

      <el-input
        v-model="searchKeyword"
        placeholder="搜索任务名称或URL"
        clearable
        style="width: 300px; margin-left: 16px"
        @keyup.enter="handleFilter"
      >
        <template #append>
          <el-button @click="handleFilter">
            <el-icon><Search /></el-icon>
          </el-button>
        </template>
      </el-input>
    </div>

    <!-- 任务表格 -->
    <el-table
      :data="tasks"
      v-loading="loading"
      stripe
      @sort-change="handleSortChange"
    >
      <el-table-column prop="name" label="任务名称" min-width="150">
        <template #default="{ row }">
          {{ row.name || '未命名任务' }}
        </template>
      </el-table-column>

      <el-table-column prop="target_url" label="目标URL" min-width="200">
        <template #default="{ row }">
          <el-tooltip :content="row.target_url" placement="top">
            <span class="text-ellipsis">{{ truncateText(row.target_url, 35) }}</span>
          </el-tooltip>
        </template>
      </el-table-column>

      <el-table-column prop="status" label="状态" width="100" sortable="custom">
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

      <el-table-column prop="created_at" label="创建时间" width="180" sortable="custom">
        <template #default="{ row }">
          {{ formatDateTime(row.created_at) }}
        </template>
      </el-table-column>

      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button
            v-if="row.status === 'pending' || row.status === 'stopped'"
            type="primary"
            size="small"
            @click="handleStart(row)"
            :loading="row._loading"
          >
            启动
          </el-button>
          <el-button
            v-if="row.status === 'running'"
            type="danger"
            size="small"
            @click="handleStop(row)"
            :loading="row._loading"
          >
            停止
          </el-button>
          <el-button
            v-if="row.status === 'completed'"
            type="success"
            size="small"
            @click="handleViewReport(row)"
          >
            报告
          </el-button>
          <el-button size="small" @click="handleViewDetail(row)">
            详情
          </el-button>
          <el-button
            v-if="['completed', 'failed', 'stopped'].includes(row.status)"
            type="danger"
            size="small"
            plain
            @click="handleDelete(row)"
            :loading="row._loading"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination-wrapper" v-if="total > 0">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handlePageSizeChange"
        @current-change="handlePageChange"
      />
    </div>

    <el-empty v-if="!loading && tasks.length === 0" description="暂无任务" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { getTaskList, startTask, stopTask, deleteTask } from '@/api/task'
import { getStatusType, getStatusText, truncateText, formatDateTime } from '@/utils/format'

const router = useRouter()

const loading = ref(false)
const tasks = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const filterStatus = ref('')
const searchKeyword = ref('')
const sortField = ref('')
const sortOrder = ref('')

// 获取任务列表
const fetchTasks = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value
    }

    if (filterStatus.value) {
      params.status = filterStatus.value
    }

    if (searchKeyword.value) {
      params.search = searchKeyword.value
    }

    if (sortField.value) {
      params.sort_by = sortField.value
      params.sort_order = sortOrder.value
    }

    const data = await getTaskList(params)
    tasks.value = (data.items || data || []).map(t => ({ ...t, _loading: false }))
    total.value = data.total || tasks.value.length
  } catch (error) {
    console.error('获取任务列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 筛选
const handleFilter = () => {
  currentPage.value = 1
  fetchTasks()
}

// 排序变化
const handleSortChange = ({ prop, order }) => {
  sortField.value = prop
  sortOrder.value = order === 'ascending' ? 'asc' : order === 'descending' ? 'desc' : ''
  fetchTasks()
}

// 页码变化
const handlePageChange = () => {
  fetchTasks()
}

// 每页数量变化
const handlePageSizeChange = () => {
  currentPage.value = 1
  fetchTasks()
}

// 启动任务
const handleStart = async (row) => {
  row._loading = true
  try {
    await startTask(row.task_id)
    ElMessage.success('任务已启动')
    fetchTasks()
  } catch (error) {
    console.error('启动失败:', error)
  } finally {
    row._loading = false
  }
}

// 停止任务
const handleStop = async (row) => {
  row._loading = true
  try {
    await stopTask(row.task_id)
    ElMessage.success('任务已停止')
    fetchTasks()
  } catch (error) {
    console.error('停止失败:', error)
  } finally {
    row._loading = false
  }
}

// 删除任务
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除此任务吗?', '提示', {
      type: 'warning'
    })

    row._loading = true
    await deleteTask(row.task_id)
    ElMessage.success('任务已删除')
    fetchTasks()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
    }
  } finally {
    row._loading = false
  }
}

// 查看详情
const handleViewDetail = (row) => {
  router.push(`/task/${row.task_id}`)
}

// 查看报告
const handleViewReport = (row) => {
  router.push(`/report/${row.task_id}`)
}

onMounted(() => {
  fetchTasks()
})
</script>

<style lang="scss" scoped>
.task-list {
  .filter-bar {
    display: flex;
    align-items: center;
    margin-bottom: 16px;
  }

  .text-ellipsis {
    display: inline-block;
    max-width: 200px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .pagination-wrapper {
    display: flex;
    justify-content: flex-end;
    margin-top: 20px;
  }
}
</style>