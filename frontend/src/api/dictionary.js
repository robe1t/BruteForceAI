import request from '@/utils/request'

/**
 * 字典相关API
 */

// 获取字典列表
export function getDictionaryList(params) {
  return request.get('/dictionaries', { params })
}

// 获取字典详情
export function getDictionary(id) {
  return request.get(`/dictionaries/${id}`)
}

// 上传字典
export function uploadDictionary(data) {
  const formData = new FormData()
  formData.append('file', data.file)
  formData.append('name', data.name)
  formData.append('type', data.type)

  return request.post('/dictionaries', formData, {
    headers: {
      'Content-Type': undefined
    }
  })
}

// 创建字典（手动输入）
export function createDictionary(data) {
  return request.post('/dictionaries', data)
}

// 更新字典
export function updateDictionary(id, data) {
  return request.put(`/dictionaries/${id}`, data)
}

// 删除字典
export function deleteDictionary(id) {
  return request.delete(`/dictionaries/${id}`)
}

// 获取字典内容
export function getDictionaryContent(id, params) {
  return request.get(`/dictionaries/${id}/content`, { params })
}

// 获取字典预览
export function previewDictionary(id, limit = 50) {
  return request.get(`/dictionaries/${id}/preview`, {
    params: { limit }
  })
}