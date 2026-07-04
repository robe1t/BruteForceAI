/**
 * 格式化工具函数
 */

/**
 * 格式化日期时间
 * @param {Date|string|number} date - 日期对象/字符串/时间戳
 * @param {string} format - 格式化模式
 */
export function formatDateTime(date, format = 'YYYY-MM-DD HH:mm:ss') {
  if (!date) return '-'

  let d = new Date(date)
  if (isNaN(d.getTime())) return '-'

  // 加8小时（UTC转北京时间）
  d = new Date(d.getTime() + 8 * 60 * 60 * 1000)

  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hours = String(d.getHours()).padStart(2, '0')
  const minutes = String(d.getMinutes()).padStart(2, '0')
  const seconds = String(d.getSeconds()).padStart(2, '0')

  return format
    .replace('YYYY', year)
    .replace('MM', month)
    .replace('DD', day)
    .replace('HH', hours)
    .replace('mm', minutes)
    .replace('ss', seconds)
}

/**
 * 格式化持续时间
 * @param {number} seconds - 秒数
 */
export function formatDuration(seconds) {
  if (!seconds || seconds < 0) return '00:00:00'

  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)

  return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
}

/**
 * 格式化文件大小
 * @param {number} bytes - 字节数
 */
export function formatFileSize(bytes) {
  if (bytes === 0) return '0 B'

  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const k = 1024
  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + units[i]
}

/**
 * 格式化数字（添加千位分隔符）
 * @param {number} num - 数字
 */
export function formatNumber(num) {
  if (num === null || num === undefined) return '-'
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

/**
 * 格式化百分比
 * @param {number} value - 值
 * @param {number} total - 总数
 * @param {number} decimals - 小数位数
 */
export function formatPercent(value, total, decimals = 0) {
  if (!total || total === 0) return '0%'
  const percent = (value / total * 100).toFixed(decimals)
  return `${percent}%`
}

/**
 * 截断文本
 * @param {string} text - 文本
 * @param {number} length - 最大长度
 */
export function truncateText(text, length = 50) {
  if (!text) return ''
  if (text.length <= length) return text
  return text.substring(0, length) + '...'
}

/**
 * 获取状态文本
 * @param {string} status - 状态码
 */
export function getStatusText(status) {
  const statusMap = {
    pending: '等待中',
    running: '运行中',
    completed: '已完成',
    stopped: '已停止',
    failed: '失败'
  }
  return statusMap[status] || status
}

/**
 * 获取状态类型（用于Element Plus Tag）
 * @param {string} status - 状态码
 */
export function getStatusType(status) {
  const typeMap = {
    pending: 'warning',
    running: 'primary',
    completed: 'success',
    stopped: 'info',
    failed: 'danger'
  }
  return typeMap[status] || 'info'
}

/**
 * 获取风险等级文本
 * @param {string} level - 风险等级
 */
export function getRiskLevelText(level) {
  const levelMap = {
    critical: '严重',
    high: '高危',
    medium: '中危',
    low: '低危',
    info: '信息'
  }
  return levelMap[level] || level
}

/**
 * 获取风险等级类型
 * @param {string} level - 风险等级
 */
export function getRiskLevelType(level) {
  const typeMap = {
    critical: 'danger',
    high: 'danger',
    medium: 'warning',
    low: 'info',
    info: ''
  }
  return typeMap[level] || 'info'
}