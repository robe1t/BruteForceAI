<template>
  <div class="config page-container">
    <div class="page-header">
      <h1 class="page-title">系统配置</h1>
    </div>

    <!-- LLM提供商配置 -->
    <div class="form-card">
      <div class="card-title">
        <span>LLM 提供商配置</span>
        <el-button type="primary" size="small" @click="showAddDialog">
          <el-icon><Plus /></el-icon>
          添加提供商
        </el-button>
      </div>

      <!-- 提供商列表 -->
      <el-table :data="providers" v-loading="loading" stripe>
        <el-table-column prop="name" label="名称" width="150">
          <template #default="{ row }">
            <span class="provider-name">{{ row.name }}</span>
            <el-tag v-if="row.is_default" type="success" size="small" style="margin-left: 8px">
              默认
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="api_key" label="API Key" min-width="200">
          <template #default="{ row }">
            <span class="api-key-mask">
              {{ row.api_key ? maskApiKey(row.api_key) : '(本地)' }}
            </span>
          </template>
        </el-table-column>

        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.connected ? 'success' : 'danger'" size="small">
              {{ row.connected ? '已连接' : '未连接' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="default_model" label="默认模型" width="200">
          <template #default="{ row }">
            {{ row.default_model || '-' }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handleTest(row)" :loading="row._testing">
              测试
            </el-button>
            <el-button size="small" @click="handleEdit(row)">
              编辑
            </el-button>
            <el-button
              size="small"
              type="danger"
              text
              @click="handleDelete(row)"
              :loading="row._deleting"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && providers.length === 0" description="暂无提供商配置" />
    </div>

    <!-- 添加/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑提供商' : '添加提供商'"
      width="500px"
      destroy-on-close
    >
      <ProviderForm
        :provider="currentProvider"
        @submit="handleSubmit"
        @cancel="dialogVisible = false"
      />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { getProviders, addProvider, updateProvider, deleteProvider, testLlmConnection } from '@/api/config'
import ProviderForm from '@/components/config/ProviderForm.vue'

const loading = ref(false)
const providers = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const currentProvider = ref(null)

// 加载提供商列表
const fetchProviders = async () => {
  loading.value = true
  try {
    const data = await getProviders()
    providers.value = (data.items || data || []).map(p => ({
      ...p,
      _testing: false,
      _deleting: false
    }))
  } catch (error) {
    console.error('获取提供商失败:', error)
  } finally {
    loading.value = false
  }
}

// 显示添加对话框
const showAddDialog = () => {
  isEdit.value = false
  currentProvider.value = null
  dialogVisible.value = true
}

// 编辑提供商
const handleEdit = (row) => {
  isEdit.value = true
  currentProvider.value = { ...row }
  dialogVisible.value = true
}

// 测试连接
const handleTest = async (row) => {
  if (!row.default_model) {
    ElMessage.warning('该提供商未配置模型名称')
    return
  }

  row._testing = true
  try {
    const result = await testLlmConnection({
      api_type: row.api_type || row.name,
      api_key: row.api_key,
      base_url: row.base_url,
      model: row.default_model
    })

    if (result.success || result.connected) {
      ElMessage.success('连接成功')
      row.connected = true
      // 更新数据库中的状态
      try {
        await updateProvider(row.name, { connected: true })
      } catch (e) {
        console.error('更新状态失败:', e)
      }
    } else {
      ElMessage.error(result.message || result.error || '连接失败')
      row.connected = false
    }
  } catch (error) {
    console.error('测试失败:', error)
    const errorMsg = error.response?.data?.error?.message || error.message || '连接失败'
    ElMessage.error(errorMsg)
    row.connected = false
  } finally {
    row._testing = false
  }
}

// 删除提供商
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除此提供商吗?', '提示', {
      type: 'warning'
    })

    row._deleting = true
    await deleteProvider(row.name)
    ElMessage.success('删除成功')
    fetchProviders()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
    }
  } finally {
    row._deleting = false
  }
}

// 提交表单
const handleSubmit = async (formData) => {
  try {
    if (isEdit.value) {
      await updateProvider(formData.name, formData)
      ElMessage.success('更新成功')
    } else {
      await addProvider(formData)
      ElMessage.success('添加成功')
    }
    dialogVisible.value = false
    fetchProviders()
  } catch (error) {
    console.error('保存失败:', error)
  }
}

// 遮蔽API Key
const maskApiKey = (key) => {
  if (!key || key.length < 8) return key
  return key.substring(0, 4) + '...' + key.substring(key.length - 4)
}

onMounted(() => {
  fetchProviders()
})
</script>

<style lang="scss" scoped>
.config {
  .card-title {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .provider-name {
    text-transform: capitalize;
    font-weight: 500;
  }

  .api-key-mask {
    font-family: monospace;
    color: #909399;
  }
}
</style>