import { defineStore } from 'pinia'
import { getProviders, addProvider, updateProvider, deleteProvider, testProvider, getModels } from '@/api/config'

export const useConfigStore = defineStore('config', {
  state: () => ({
    providers: [],
    currentProvider: null,
    models: [],
    loading: false
  }),

  getters: {
    // 已配置的提供商
    configuredProviders: (state) => state.providers.filter(p => p.configured),
    // 默认提供商
    defaultProvider: (state) => state.providers.find(p => p.is_default)
  },

  actions: {
    /**
     * 获取提供商列表
     */
    async fetchProviders() {
      this.loading = true
      try {
        const data = await getProviders()
        this.providers = data.items || data || []
        return this.providers
      } catch (error) {
        console.error('获取提供商列表失败:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * 添加提供商
     */
    async addProviderConfig(data) {
      try {
        const result = await addProvider(data)
        await this.fetchProviders()
        return result
      } catch (error) {
        console.error('添加提供商失败:', error)
        throw error
      }
    },

    /**
     * 更新提供商
     */
    async updateProviderConfig(name, data) {
      try {
        const result = await updateProvider(name, data)
        await this.fetchProviders()
        return result
      } catch (error) {
        console.error('更新提供商失败:', error)
        throw error
      }
    },

    /**
     * 删除提供商
     */
    async deleteProviderConfig(name) {
      try {
        await deleteProvider(name)
        await this.fetchProviders()
      } catch (error) {
        console.error('删除提供商失败:', error)
        throw error
      }
    },

    /**
     * 测试提供商连接
     */
    async testProviderConnection(name) {
      try {
        const result = await testProvider(name)
        return result
      } catch (error) {
        console.error('测试连接失败:', error)
        throw error
      }
    },

    /**
     * 获取可用模型列表
     */
    async fetchModels(provider) {
      try {
        const data = await getModels(provider)
        this.models = data.models || data || []
        return this.models
      } catch (error) {
        console.error('获取模型列表失败:', error)
        throw error
      }
    },

    /**
     * 设置当前提供商
     */
    setCurrentProvider(provider) {
      this.currentProvider = provider
    }
  }
})