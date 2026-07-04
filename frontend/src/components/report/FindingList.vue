<template>
  <div class="finding-list">
    <div class="list-header" v-if="title">
      <span class="list-title">{{ title }}</span>
      <el-badge :value="findings.length" type="danger" v-if="findings.length > 0" />
    </div>

    <div class="list-content" v-if="findings.length > 0">
      <div
        v-for="(finding, index) in findings"
        :key="index"
        class="finding-item"
        :class="`finding-${finding.level}`"
      >
        <div class="finding-level">
          <el-tag :type="getRiskLevelType(finding.level)" size="small">
            {{ getRiskLevelText(finding.level) }}
          </el-tag>
        </div>
        <div class="finding-content">
          <div class="finding-title">{{ finding.title }}</div>
          <div class="finding-desc" v-if="finding.description">
            {{ finding.description }}
          </div>
          <div class="finding-evidence" v-if="finding.evidence">
            <code>{{ finding.evidence }}</code>
          </div>
        </div>
      </div>
    </div>

    <el-empty v-else description="暂无发现" :image-size="60" />
  </div>
</template>

<script setup>
import { getRiskLevelText, getRiskLevelType } from '@/utils/format'

defineProps({
  title: {
    type: String,
    default: ''
  },
  findings: {
    type: Array,
    default: () => []
  }
})
</script>

<style lang="scss" scoped>
.finding-list {
  background: #fff;
  border-radius: 8px;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;

  .list-title {
    font-size: 16px;
    font-weight: 600;
    color: #303133;
  }
}

.list-content {
  .finding-item {
    display: flex;
    gap: 12px;
    padding: 16px;
    border-radius: 8px;
    margin-bottom: 12px;
    border: 1px solid #ebeef5;

    &:last-child {
      margin-bottom: 0;
    }

    &.finding-critical {
      background: #fef0f0;
      border-color: #fbc4c4;
    }

    &.finding-high {
      background: #fdf6ec;
      border-color: #f5dab1;
    }

    &.finding-medium {
      background: #fdf6ec;
      border-color: #faecd8;
    }

    &.finding-low {
      background: #f4f4f5;
      border-color: #e9e9eb;
    }
  }

  .finding-level {
    flex-shrink: 0;
  }

  .finding-content {
    flex: 1;

    .finding-title {
      font-weight: 600;
      color: #303133;
      margin-bottom: 4px;
    }

    .finding-desc {
      font-size: 14px;
      color: #606266;
      margin-bottom: 8px;
    }

    .finding-evidence {
      background: #f5f7fa;
      padding: 8px 12px;
      border-radius: 4px;
      font-size: 13px;

      code {
        color: #e6a23c;
        word-break: break-all;
      }
    }
  }
}
</style>