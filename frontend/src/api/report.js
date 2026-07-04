import request from '@/utils/request'

/**
 * 报告相关API
 */

// 获取测试报告
export function getReport(taskId) {
  return request.get(`/reports/${taskId}`)
}

// 导出报告
export function exportReport(taskId, format = 'pdf') {
  return request.get(`/reports/${taskId}/export`, {
    params: { format },
    responseType: 'blob'
  })
}

// 获取报告摘要
export function getReportSummary(taskId) {
  return request.get(`/reports/${taskId}/summary`)
}

// 获取发现列表
export function getFindings(taskId, params) {
  return request.get(`/reports/${taskId}/findings`, { params })
}

// 获取修复建议
export function getRecommendations(taskId) {
  return request.get(`/reports/${taskId}/recommendations`)
}