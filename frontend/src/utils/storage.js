/**
 * 本地存储工具类
 */

const STORAGE_PREFIX = 'bfa_'

/**
 * 设置本地存储
 * @param {string} key - 键名
 * @param {any} value - 值
 */
export function setStorage(key, value) {
  try {
    const data = JSON.stringify(value)
    localStorage.setItem(STORAGE_PREFIX + key, data)
  } catch (error) {
    console.error('存储失败:', error)
  }
}

/**
 * 获取本地存储
 * @param {string} key - 键名
 * @param {any} defaultValue - 默认值
 */
export function getStorage(key, defaultValue = null) {
  try {
    const data = localStorage.getItem(STORAGE_PREFIX + key)
    return data ? JSON.parse(data) : defaultValue
  } catch (error) {
    console.error('读取存储失败:', error)
    return defaultValue
  }
}

/**
 * 移除本地存储
 * @param {string} key - 键名
 */
export function removeStorage(key) {
  localStorage.removeItem(STORAGE_PREFIX + key)
}

/**
 * 清空所有本地存储
 */
export function clearStorage() {
  const keys = Object.keys(localStorage)
  keys.forEach(key => {
    if (key.startsWith(STORAGE_PREFIX)) {
      localStorage.removeItem(key)
    }
  })
}