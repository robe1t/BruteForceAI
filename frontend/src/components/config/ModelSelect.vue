<template>
  <div class="model-select">
    <el-select
      v-model="selectedModel"
      :placeholder="placeholder"
      :loading="loading"
      :disabled="disabled"
      filterable
      @change="handleChange"
    >
      <el-option
        v-for="model in modelList"
        :key="model.id || model"
        :label="model.name || model"
        :value="model.id || model"
      >
        <div class="model-option">
          <span class="model-name">{{ model.name || model }}</span>
          <span class="model-id" v-if="model.id">{{ model.id }}</span>
        </div>
      </el-option>
    </el-select>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { getModels } from '@/api/config'

const props = defineProps({
  provider: {
    type: String,
    required: true
  },
  modelValue: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: '请选择模型'
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

const loading = ref(false)
const modelList = ref([])

// 选中的模型
const selectedModel = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// 加载模型列表
const loadModels = async () => {
  if (!props.provider) {
    modelList.value = []
    return
  }

  loading.value = true
  try {
    const data = await getModels(props.provider)
    modelList.value = data.models || data || []

    // 默认选择第一个模型
    if (modelList.value.length > 0 && !selectedModel.value) {
      selectedModel.value = modelList.value[0].id || modelList.value[0]
    }
  } catch (error) {
    console.error('加载模型失败:', error)
    modelList.value = []
  } finally {
    loading.value = false
  }
}

// 模型变化
const handleChange = (value) => {
  emit('change', value)
}

// 监听提供商变化
watch(() => props.provider, () => {
  loadModels()
}, { immediate: true })

onMounted(() => {
  loadModels()
})
</script>

<style lang="scss" scoped>
.model-select {
  width: 100%;
}

.model-option {
  display: flex;
  justify-content: space-between;
  align-items: center;

  .model-name {
    font-weight: 500;
  }

  .model-id {
    font-size: 12px;
    color: #909399;
  }
}
</style>