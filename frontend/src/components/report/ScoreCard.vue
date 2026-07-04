<template>
  <div class="score-card" :class="`score-level-${scoreLevel}`">
    <div class="score-header">
      <span class="score-label">{{ title }}</span>
      <el-tag :type="scoreTagType" size="small">{{ scoreLevelText }}</el-tag>
    </div>
    <div class="score-content">
      <div class="score-value">
        <span class="value-number">{{ score }}</span>
        <span class="value-total">/100</span>
      </div>
      <el-progress
        :percentage="score"
        :stroke-width="8"
        :show-text="false"
        :color="scoreColor"
      />
    </div>
    <div class="score-desc" v-if="description">
      {{ description }}
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: {
    type: String,
    default: '安全评分'
  },
  score: {
    type: Number,
    default: 0
  },
  description: {
    type: String,
    default: ''
  }
})

// 评分等级
const scoreLevel = computed(() => {
  if (props.score >= 80) return 'high'
  if (props.score >= 60) return 'medium'
  if (props.score >= 40) return 'low'
  return 'critical'
})

// 评分等级文本
const scoreLevelText = computed(() => {
  const levels = {
    high: '安全',
    medium: '中等风险',
    low: '高风险',
    critical: '严重风险'
  }
  return levels[scoreLevel.value]
})

// 评分标签类型
const scoreTagType = computed(() => {
  const types = {
    high: 'success',
    medium: 'warning',
    low: 'danger',
    critical: 'danger'
  }
  return types[scoreLevel.value]
})

// 评分颜色
const scoreColor = computed(() => {
  const colors = {
    high: '#67c23a',
    medium: '#e6a23c',
    low: '#f56c6c',
    critical: '#c45656'
  }
  return colors[scoreLevel.value]
})
</script>

<style lang="scss" scoped>
.score-card {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  border: 1px solid #ebeef5;
  transition: transform 0.3s;

  &:hover {
    transform: translateY(-2px);
  }

  &.score-level-high {
    border-left: 4px solid #67c23a;
  }

  &.score-level-medium {
    border-left: 4px solid #e6a23c;
  }

  &.score-level-low {
    border-left: 4px solid #f56c6c;
  }

  &.score-level-critical {
    border-left: 4px solid #c45656;
  }
}

.score-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;

  .score-label {
    font-size: 16px;
    font-weight: 600;
    color: #303133;
  }
}

.score-content {
  margin-bottom: 12px;

  .score-value {
    margin-bottom: 12px;

    .value-number {
      font-size: 48px;
      font-weight: 700;
      color: #303133;
    }

    .value-total {
      font-size: 24px;
      color: #909399;
    }
  }
}

.score-desc {
  font-size: 14px;
  color: #606266;
  line-height: 1.5;
}
</style>