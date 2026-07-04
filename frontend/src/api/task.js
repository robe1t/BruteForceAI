import request from '@/utils/request'

/**
 * 任务相关API
 */

// 创建任务
export function createTask(data) {
  return request.post('/tasks', data)
}

// 获取任务列表
export function getTaskList(params) {
  return request.get('/tasks', { params })
}

// 获取任务详情
export function getTaskDetail(taskId) {
  return request.get(`/tasks/${taskId}`)
}

// 启动任务
export function startTask(taskId) {
  return request.post(`/tasks/${taskId}/start`)
}

// 停止任务
export function stopTask(taskId) {
  return request.post(`/tasks/${taskId}/stop`)
}

// 暂停任务
export function pauseTask(taskId) {
  return request.post(`/tasks/${taskId}/pause`)
}

// 恢复任务
export function resumeTask(taskId) {
  return request.post(`/tasks/${taskId}/resume`)
}

// 删除任务
export function deleteTask(taskId) {
  return request.delete(`/tasks/${taskId}`)
}

// 获取任务进度
export function getTaskProgress(taskId) {
  return request.get(`/tasks/${taskId}/progress`)
}

// 获取任务日志
export function getTaskLogs(taskId, params) {
  return request.get(`/tasks/${taskId}/logs`, { params })
}

// 获取概览统计
export function getOverviewStats() {
  return request.get('/stats/overview')
}