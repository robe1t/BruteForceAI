<template>
  <div class="report page-container" v-loading="loading">
    <div class="page-header">
      <div class="header-left">
        <el-button text @click="$router.back()">
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <h1 class="page-title">安全审计报告</h1>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="handleExport('html')" :loading="exportLoading">
          <el-icon><Download /></el-icon>
          导出HTML报告
        </el-button>
      </div>
    </div>

    <!-- 目标信息 -->
    <div class="form-card" v-if="report">
      <div class="card-title">目标信息</div>
      <el-descriptions :column="3" border>
        <el-descriptions-item label="目标URL">
          <el-link :href="report.target_url" target="_blank" type="primary">
            {{ report.target_url }}
          </el-link>
        </el-descriptions-item>
        <el-descriptions-item label="任务名称">
          {{ report.task_name || '未命名任务' }}
        </el-descriptions-item>
        <el-descriptions-item label="扫描时间">
          {{ formatDateTime(report.scan_time) }}
        </el-descriptions-item>
      </el-descriptions>
    </div>

    <!-- 安全评分 -->
    <div class="form-card" v-if="report">
      <div class="card-title">安全评分</div>
      <div class="score-section">
        <div class="score-main">
          <div class="score-circle" :style="{ borderColor: getScoreColor(report.score || 0) }">
            <span class="score-number" :style="{ color: getScoreColor(report.score || 0) }">
              {{ report.score || 0 }}
            </span>
            <span class="score-unit">分</span>
          </div>
          <div class="score-desc">{{ report.score_description || '安全评估完成' }}</div>
        </div>
        <div class="score-details">
          <div
            v-for="(item, key) in report.score_details"
            :key="key"
            class="score-detail-item"
          >
            <div class="detail-header">
              <span class="detail-label">{{ item.label || key }}</span>
              <span class="detail-score" :style="{ color: getScoreColor(item.score) }">
                {{ item.score }}/100
              </span>
            </div>
            <el-progress
              :percentage="item.score"
              :stroke-width="8"
              :show-text="false"
              :color="getScoreColor(item.score)"
            />
            <div class="detail-desc" v-if="item.description">
              {{ item.description }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 发现的漏洞 -->
    <div class="form-card" v-if="report && report.findings && report.findings.length > 0">
      <div class="card-title">发现的漏洞</div>
      <FindingList :findings="report.findings || []" />
    </div>

    <!-- 发现的弱口令 -->
    <div class="form-card" v-if="report?.credentials?.length > 0">
      <div class="card-title">
        发现的弱口令
        <el-badge :value="report.credentials.length" type="danger" />
      </div>
      <el-table :data="report.credentials" stripe>
        <el-table-column prop="username" label="用户名" width="200" />
        <el-table-column prop="password" label="密码" width="200" />
        <el-table-column prop="found_at" label="发现时间">
          <template #default="{ row }">
            {{ formatDateTime(row.found_at) }}
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 修复建议 -->
    <div class="form-card" v-if="report?.recommendations?.length > 0">
      <div class="card-title">修复建议</div>
      <div class="recommendations">
        <div
          v-for="(rec, index) in report.recommendations"
          :key="index"
          class="recommendation-item"
        >
          <div class="rec-number">{{ index + 1 }}</div>
          <div class="rec-content">{{ rec }}</div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <el-empty v-if="!loading && !report" description="报告不存在" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getReport, exportReport } from '@/api/report'
import { formatDateTime } from '@/utils/format'
import FindingList from '@/components/report/FindingList.vue'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const exportLoading = ref(false)
const report = ref(null)

// 获取报告
const fetchReport = async () => {
  loading.value = true
  try {
    report.value = await getReport(route.params.id)
  } catch (error) {
    console.error('获取报告失败:', error)
    ElMessage.error('获取报告失败')
  } finally {
    loading.value = false
  }
}

// 导出报告
const handleExport = async (format) => {
  exportLoading.value = true
  try {
    const blob = await exportReport(route.params.id, format)

    // 创建下载链接
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `report_${route.params.id}.${format}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    ElMessage.success('导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  } finally {
    exportLoading.value = false
  }
}

// 获取评分颜色
const getScoreColor = (score) => {
  if (score >= 80) return '#67c23a'
  if (score >= 60) return '#e6a23c'
  if (score >= 40) return '#f56c6c'
  return '#c45656'
}

onMounted(() => {
  fetchReport()
})
</script>

<style lang="scss" scoped>
.report {
  max-width: 1000px;
  margin: 0 auto;

  .header-left {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .score-section {
    display: flex;
    gap: 40px;
    align-items: center;

    .score-main {
      text-align: center;
      flex-shrink: 0;

      .score-circle {
        width: 120px;
        height: 120px;
        border-radius: 50%;
        border: 8px solid #67c23a;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin-bottom: 12px;

        .score-number {
          font-size: 36px;
          font-weight: 700;
          line-height: 1;
        }

        .score-unit {
          font-size: 14px;
          color: #909399;
        }
      }

      .score-desc {
        font-size: 14px;
        color: #606266;
      }
    }

    .score-details {
      flex: 1;

      .score-detail-item {
        margin-bottom: 16px;

        &:last-child {
          margin-bottom: 0;
        }

        .detail-header {
          display: flex;
          justify-content: space-between;
          margin-bottom: 8px;

          .detail-label {
            font-weight: 500;
            color: #303133;
          }

          .detail-score {
            font-weight: 600;
          }
        }

        .detail-desc {
          font-size: 13px;
          color: #909399;
          margin-top: 4px;
        }
      }
    }
  }

  .recommendations {
    .recommendation-item {
      display: flex;
      gap: 12px;
      padding: 16px;
      background: #f5f7fa;
      border-radius: 8px;
      margin-bottom: 12px;

      &:last-child {
        margin-bottom: 0;
      }

      .rec-number {
        width: 28px;
        height: 28px;
        background: #409eff;
        color: #fff;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        flex-shrink: 0;
      }

      .rec-content {
        flex: 1;
        line-height: 1.6;
        color: #606266;
      }
    }
  }
}
</style>