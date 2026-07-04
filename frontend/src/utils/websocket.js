import { io } from 'socket.io-client'

/**
 * WebSocket客户端封装类
 * 用于与后端实时通信，接收任务进度、日志等信息
 */
class WebSocketClient {
  constructor() {
    this.socket = null
    this.listeners = new Map()
    this.connected = false
  }

  /**
   * 连接WebSocket服务器
   * @param {string} url - WebSocket服务器地址
   */
  connect(url = import.meta.env.VITE_WS_URL || 'ws://localhost:5000') {
    // 已连接则不重复连接
    if (this.socket?.connected) {
      return
    }

    this.socket = io(url, {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000
    })

    // 连接成功
    this.socket.on('connect', () => {
      console.log('WebSocket已连接')
      this.connected = true
      this.emit('connected', { connected: true })
    })

    // 连接断开
    this.socket.on('disconnect', () => {
      console.log('WebSocket已断开')
      this.connected = false
      this.emit('disconnected', { connected: false })
    })

    // 连接错误
    this.socket.on('connect_error', (error) => {
      console.error('WebSocket连接错误:', error)
      this.emit('error', { error: error.message })
    })

    // 任务状态变化
    this.socket.on('task_status', (data) => {
      this.emit('task_status', data)
    })

    // 任务进度更新
    this.socket.on('task_progress', (data) => {
      this.emit('task_progress', data)
    })

    // 发现弱口令
    this.socket.on('credential_found', (data) => {
      this.emit('credential_found', data)
    })

    // 实时日志
    this.socket.on('log', (data) => {
      this.emit('log', data)
    })

    // 任务完成
    this.socket.on('task_completed', (data) => {
      this.emit('task_completed', data)
    })
  }

  /**
   * 订阅任务更新
   * @param {string} taskId - 任务ID
   */
  subscribe(taskId) {
    if (this.socket?.connected) {
      this.socket.emit('subscribe', { task_id: taskId })
    }
  }

  /**
   * 取消订阅任务
   * @param {string} taskId - 任务ID
   */
  unsubscribe(taskId) {
    if (this.socket?.connected) {
      this.socket.emit('unsubscribe', { task_id: taskId })
    }
  }

  /**
   * 注册事件监听器
   * @param {string} event - 事件名称
   * @param {Function} callback - 回调函数
   */
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set())
    }
    this.listeners.get(event).add(callback)
  }

  /**
   * 移除事件监听器
   * @param {string} event - 事件名称
   * @param {Function} callback - 回调函数
   */
  off(event, callback) {
    if (callback) {
      this.listeners.get(event)?.delete(callback)
    } else {
      this.listeners.delete(event)
    }
  }

  /**
   * 触发事件
   * @param {string} event - 事件名称
   * @param {any} data - 事件数据
   */
  emit(event, data) {
    this.listeners.get(event)?.forEach(callback => {
      try {
        callback(data)
      } catch (error) {
        console.error(`事件处理错误 [${event}]:`, error)
      }
    })
  }

  /**
   * 断开WebSocket连接
   */
  disconnect() {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
      this.connected = false
      this.listeners.clear()
    }
  }

  /**
   * 获取连接状态
   */
  isConnected() {
    return this.connected && this.socket?.connected
  }
}

// 导出单例
export default new WebSocketClient()