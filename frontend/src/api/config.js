import request from '@/utils/request'

/**
 * 系统配置相关API
 */

// 获取所有提供商配置
export function getProviders() {
  return request.get('/config/providers')
}

// 获取单个提供商配置
export function getProvider(name) {
  return request.get(`/config/providers/${name}`)
}

// 添加提供商
export function addProvider(data) {
  return request.post('/config/providers', data)
}

// 更新提供商
export function updateProvider(name, data) {
  return request.put(`/config/providers/${name}`, data)
}

// 删除提供商
export function deleteProvider(name) {
  return request.delete(`/config/providers/${name}`)
}

// 测试已保存提供商连接
export function testProvider(name) {
  return request.post(`/config/providers/${name}/test`)
}

// 测试LLM连接（不需要保存到数据库）
export function testLlmConnection(data) {
  return request.post('/config/test-llm', {
    api_type: data.api_type || data.name || 'openai',
    api_key: data.api_key,
    base_url: data.base_url,
    model: data.default_model || data.model
  })
}

// 获取示例模型名称（仅供参考）
export function getExampleModels() {
  return request.get('/config/example-models')
}

// 设置默认提供商
export function setDefaultProvider(name) {
  return request.put(`/config/providers/${name}/default`)
}