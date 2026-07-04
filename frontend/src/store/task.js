import { defineStore } from 'pinia'
import { getTaskList, getTaskDetail, getOverviewStats } from '@/api/task'
import websocket from '@/utils/websocket'

export const useTaskStore = defineStore('task', {
  state: () => ({
    tasks: [],
    currentTask: null,
    stats: {
      total: 0,
      running: 0,
      completed: 0,
      weakPwd: 0
    },
    loading: false,
    // 实时日志
    logs: [],
    // 发现的弱口令
    credentials: [],
    // WebSocket连接状态
    wsConnected: false
  }),

  getters: {
    // 运行中的任务
    runningTasks: (state) => state.tasks.filter(t => t.status === 'running'),
    // 等待中的任务
    pendingTasks: (state) => state.tasks.filter(t => t.status === 'pending'),
    // 已完成的任务
    completedTasks: (state) => state.tasks.filter(t => t.status === 'completed')
  },

  actions: {
    /**
     * 获取任务列表
     */
    async fetchTasks(params = {}) {
      this.loading = true
      try {
        const data = await getTaskList(params)
        // 兼容不同的响应格式
        this.tasks = data.items || data || []
        return data
      } catch (error) {
        console.error('获取任务列表失败:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * 获取任务详情
     */
    async fetchTaskDetail(taskId) {
      this.loading = true
      try {
        this.currentTask = await getTaskDetail(taskId)
        return this.currentTask
      } catch (error) {
        console.error('获取任务详情失败:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * 获取概览统计
     */
    async fetchStats() {
      try {
        const data = await getOverviewStats()
        this.stats = {
          total: data.total || 0,
          running: data.running || 0,
          completed: data.completed || 0,
          weakPwd: data.weak_credentials || 0
        }
        return data
      } catch (error) {
        console.error('获取统计失败:', error)
        throw error
      }
    },

    /**
     * 订阅任务更新
     */
    subscribeTask(taskId) {
      // 清空之前的日志和凭证
      this.logs = []
      this.credentials = []

      // 订阅WebSocket事件
      websocket.subscribe(taskId)

      // 监听进度更新
      websocket.on('task_progress', (data) => {
        if (this.currentTask && data.task_id === this.currentTask.id) {
          this.currentTask.progress = data.progress
          this.currentTask.current_index = data.current_index
          this.currentTask.total_count = data.total_count
        }
      })

      // 监听状态变化
      websocket.on('task_status', (data) => {
        if (this.currentTask && data.task_id === this.currentTask.id) {
          this.currentTask.status = data.status
        }
        // 更新列表中的状态
        const task = this.tasks.find(t => t.id === data.task_id)
        if (task) {
          task.status = data.status
        }
      })

      // 监听发现弱口令
      websocket.on('credential_found', (data) => {
        this.credentials.push({
          username: data.username,
          password: data.password,
          time: new Date().toLocaleTimeString()
        })
      })

      // 监听日志
      websocket.on('log', (data) => {
        this.logs.push({
          time: data.timestamp || new Date().toLocaleTimeString(),
          level: data.level || 'info',
          message: data.message
        })
        // 限制日志数量
        if (this.logs.length > 500) {
          this.logs = this.logs.slice(-500)
        }
      })

      // 监听任务完成
      websocket.on('task_completed', (data) => {
        if (this.currentTask && data.task_id === this.currentTask.id) {
          this.currentTask.status = 'completed'
          this.currentTask.progress = 100
        }
      })
    },

    /**
     * 取消订阅任务
     */
    unsubscribeTask(taskId) {
      websocket.unsubscribe(taskId)
      websocket.off('task_progress')
      websocket.off('task_status')
      websocket.off('credential_found')
      websocket.off('log')
      websocket.off('task_completed')
    },

    /**
     * 清空日志
     */
    clearLogs() {
      this.logs = []
    },

    /**
     * 设置WebSocket连接状态
     */
    setWsConnected(connected) {
      this.wsConnected = connected
    }
  }
})