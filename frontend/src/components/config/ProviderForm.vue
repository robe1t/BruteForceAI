<template>
  <el-form
    ref="formRef"
    :model="formData"
    :rules="rules"
    label-width="100px"
    class="provider-form"
  >
    <el-form-item label="提供商类型" prop="name">
      <el-select v-model="formData.name" placeholder="请选择提供商" :disabled="isEdit" @change="handleProviderChange">
        <el-option label="Anthropic" value="anthropic" />
        <el-option label="OpenAI" value="openai" />
        <el-option label="Groq" value="groq" />
        <el-option label="Ollama" value="ollama" />
        <el-option label="Azure OpenAI" value="azure" />
      </el-select>
    </el-form-item>

    <el-form-item label="API Key" prop="api_key">
      <el-input
        v-model="formData.api_key"
        type="password"
        placeholder="请输入API Key"
        show-password
      />
    </el-form-item>

    <el-form-item label="API地址">
      <el-input
        v-model="formData.base_url"
        placeholder="可选，默认使用官方地址"
        clearable
      />
    </el-form-item>

    <el-form-item label="默认模型" prop="default_model">
      <el-input
        v-model="formData.default_model"
        placeholder="请输入模型名称"
        clearable
      />
      <div class="model-tips" v-if="exampleModels.length > 0">
        <span class="tips-label">示例模型：</span>
        <el-tag
          v-for="model in exampleModels"
          :key="model"
          size="small"
          class="model-tag"
          @click="selectModel(model)"
        >
          {{ model }}
        </el-tag>
      </div>
    </el-form-item>

    <el-form-item>
      <el-button @click="handleTest" :loading="testing">
        测试连接
      </el-button>
      <el-button type="primary" @click="handleSubmit" :loading="loading">
        保存
      </el-button>
      <el-button @click="handleCancel">取消</el-button>
    </el-form-item>
  </el-form>
</template>

<script setup>
import { ref, reactive, watch, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { testProvider, testLlmConnection, getExampleModels } from '@/api/config'

const props = defineProps({
  provider: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['submit', 'cancel'])

const formRef = ref(null)
const loading = ref(false)
const testing = ref(false)
const isEdit = ref(false)

// 示例模型数据
const allExampleModels = ref({})

// 当前提供商的示例模型
const exampleModels = computed(() => {
  return allExampleModels.value[formData.name] || []
})

// 表单数据
const formData = reactive({
  name: '',
  api_key: '',
  base_url: '',
  default_model: ''
})

// 表单验证规则
const rules = {
  name: [
    { required: true, message: '请选择提供商', trigger: 'change' }
  ],
  api_key: [
    { required: true, message: '请输入API Key', trigger: 'blur' }
  ],
  default_model: [
    { required: true, message: '请输入模型名称', trigger: 'blur' }
  ]
}

// 提供商变化时清空模型
const handleProviderChange = () => {
  formData.default_model = ''
}

// 选择示例模型
const selectModel = (model) => {
  formData.default_model = model
}

// 加载示例模型
const loadExampleModels = async () => {
  try {
    const data = await getExampleModels()
    allExampleModels.value = data.models || {}
  } catch (error) {
    console.error('加载示例模型失败:', error)
  }
}

// 测试连接
const handleTest = async () => {
  if (!formData.api_key) {
    ElMessage.warning('请先输入API Key')
    return
  }

  if (!formData.default_model) {
    ElMessage.warning('请先输入模型名称')
    return
  }

  testing.value = true
  try {
    let result

    if (isEdit.value) {
      // 编辑模式：测试已保存的提供商
      result = await testProvider(formData.name)
    } else {
      // 新增模式：使用当前表单数据测试
      console.log('[ProviderForm] Testing with:', {
        api_type: formData.name,
        api_key: '***',
        base_url: formData.base_url,
        model: formData.default_model
      })
      result = await testLlmConnection({
        api_type: formData.name,  // openai, anthropic, etc.
        api_key: formData.api_key,
        base_url: formData.base_url,
        model: formData.default_model
      })
    }

    console.log('[ProviderForm] Test result:', result)

    if (result.success || result.connected) {
      ElMessage.success('连接成功')
    } else {
      // 显示详细错误信息
      const errorMsg = result.error?.message || result.message || result.error || '连接失败'
      ElMessage.error(errorMsg)
    }
  } catch (error) {
    console.error('测试失败:', error)
    // 显示更详细的错误信息
    const errorMsg = error.response?.data?.error?.message || error.message || '测试连接失败'
    ElMessage.error(errorMsg)
  } finally {
    testing.value = false
  }
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    emit('submit', { ...formData })
  } catch (error) {
    console.error('验证失败:', error)
  }
}

// 取消
const handleCancel = () => {
  emit('cancel')
}

// 初始化
const initForm = () => {
  if (props.provider) {
    isEdit.value = true
    formData.name = props.provider.name || ''
    formData.api_key = props.provider.api_key || ''
    formData.base_url = props.provider.base_url || ''
    formData.default_model = props.provider.default_model || ''
  }
}

onMounted(() => {
  initForm()
  loadExampleModels()
})

// 监听provider变化
watch(() => props.provider, () => {
  initForm()
}, { deep: true })
</script>

<style lang="scss" scoped>
.provider-form {
  max-width: 500px;
}

.model-tips {
  margin-top: 8px;

  .tips-label {
    font-size: 12px;
    color: #909399;
    margin-right: 8px;
  }

  .model-tag {
    margin-right: 4px;
    margin-bottom: 4px;
    cursor: pointer;

    &:hover {
      opacity: 0.8;
    }
  }
}
</style>