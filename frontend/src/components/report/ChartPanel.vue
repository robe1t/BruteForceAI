<template>
  <div class="chart-panel" ref="chartRef"></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  type: {
    type: String,
    default: 'pie' // pie, bar, radar
  },
  title: {
    type: String,
    default: ''
  },
  data: {
    type: Array,
    default: () => []
  },
  options: {
    type: Object,
    default: () => ({})
  }
})

const chartRef = ref(null)
let chartInstance = null

// 初始化图表
const initChart = () => {
  if (!chartRef.value) return

  chartInstance = echarts.init(chartRef.value)
  updateChart()
}

// 更新图表
const updateChart = () => {
  if (!chartInstance) return

  let option = {}

  switch (props.type) {
    case 'pie':
      option = getPieOption()
      break
    case 'bar':
      option = getBarOption()
      break
    case 'radar':
      option = getRadarOption()
      break
    default:
      option = getPieOption()
  }

  // 合并自定义选项
  option = { ...option, ...props.options }
  chartInstance.setOption(option)
}

// 饼图配置
const getPieOption = () => ({
  title: {
    text: props.title,
    left: 'center',
    textStyle: {
      fontSize: 14,
      fontWeight: 'normal'
    }
  },
  tooltip: {
    trigger: 'item',
    formatter: '{b}: {c} ({d}%)'
  },
  legend: {
    orient: 'vertical',
    right: 10,
    top: 'center'
  },
  series: [
    {
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['40%', '50%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 10,
        borderColor: '#fff',
        borderWidth: 2
      },
      label: {
        show: false
      },
      emphasis: {
        label: {
          show: true,
          fontSize: 16,
          fontWeight: 'bold'
        }
      },
      labelLine: {
        show: false
      },
      data: props.data.map((item, index) => ({
        ...item,
        itemStyle: {
          color: getChartColor(index)
        }
      }))
    }
  ]
})

// 柱状图配置
const getBarOption = () => ({
  title: {
    text: props.title,
    left: 'center',
    textStyle: {
      fontSize: 14,
      fontWeight: 'normal'
    }
  },
  tooltip: {
    trigger: 'axis'
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    containLabel: true
  },
  xAxis: {
    type: 'category',
    data: props.data.map(item => item.name)
  },
  yAxis: {
    type: 'value'
  },
  series: [
    {
      data: props.data.map((item, index) => ({
        value: item.value,
        itemStyle: {
          color: getChartColor(index)
        }
      })),
      type: 'bar',
      barWidth: '60%'
    }
  ]
})

// 雷达图配置
const getRadarOption = () => ({
  title: {
    text: props.title,
    left: 'center',
    textStyle: {
      fontSize: 14,
      fontWeight: 'normal'
    }
  },
  tooltip: {},
  radar: {
    indicator: props.data.map(item => ({
      name: item.name,
      max: item.max || 100
    }))
  },
  series: [
    {
      type: 'radar',
      data: [
        {
          value: props.data.map(item => item.value),
          areaStyle: {
            color: 'rgba(64, 158, 255, 0.3)'
          },
          lineStyle: {
            color: '#409eff'
          },
          itemStyle: {
            color: '#409eff'
          }
        }
      ]
    }
  ]
})

// 获取图表颜色
const getChartColor = (index) => {
  const colors = [
    '#67c23a', // 绿色 - 安全
    '#e6a23c', // 橙色 - 警告
    '#f56c6c', // 红色 - 危险
    '#409eff', // 蓝色 - 信息
    '#909399', // 灰色 - 其他
    '#c45656'  // 深红 - 严重
  ]
  return colors[index % colors.length]
}

// 处理窗口大小变化
const handleResize = () => {
  chartInstance?.resize()
}

// 监听数据变化
watch(() => props.data, () => {
  updateChart()
}, { deep: true })

onMounted(() => {
  initChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
})
</script>

<style lang="scss" scoped>
.chart-panel {
  width: 100%;
  height: 300px;
}
</style>