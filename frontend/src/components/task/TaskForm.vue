<template>
  <el-form
    ref="formRef"
    :model="formData"
    :rules="rules"
    label-width="100px"
    class="task-form"
  >
    <!-- 目标信息 -->
    <el-form-item label="目标URL" prop="target_url">
      <el-input
        v-model="formData.target_url"
        placeholder="请输入目标登录页面URL"
        clearable
      >
        <template #prepend>
          <el-select v-model="urlProtocol" style="width: 80px">
            <el-option label="http://" value="http://" />
            <el-option label="https://" value="https://" />
          </el-select>
        </template>
      </el-input>
    </el-form-item>

    <el-form-item label="任务名称" prop="name">
      <el-input
        v-model="formData.name"
        placeholder="请输入任务名称（可选）"
        clearable
      />
    </el-form-item>

    <!-- 用户名字典 -->
    <el-form-item label="用户名字典" prop="username_dict">
      <el-radio-group v-model="usernameType" @change="handleUsernameTypeChange">
        <el-radio value="select">选择已有字典</el-radio>
        <el-radio value="upload">上传新字典</el-radio>
        <el-radio value="manual">手动输入</el-radio>
      </el-radio-group>

      <!-- 选择已有字典 -->
      <el-select
        v-if="usernameType === 'select'"
        v-model="formData.username_dict_id"
        placeholder="请选择用户名字典"
        style="width: 100%; margin-top: 8px"
      >
        <el-option
          v-for="dict in usernameDictionaries"
          :key="dict.id"
          :label="dict.name"
          :value="dict.id"
        />
      </el-select>

      <!-- 上传字典 -->
      <el-upload
        v-if="usernameType === 'upload'"
        ref="usernameUploadRef"
        :auto-upload="false"
        :limit="1"
        accept=".txt"
        :on-change="handleUsernameFileChange"
        style="margin-top: 8px"
      >
        <el-button type="primary">选择文件</el-button>
        <template #tip>
          <div class="el-upload__tip">支持 .txt 格式，每行一个用户名</div>
        </template>
      </el-upload>

      <!-- 手动输入 -->
      <el-input
        v-if="usernameType === 'manual'"
        v-model="formData.username_list"
        type="textarea"
        :rows="4"
        placeholder="每行输入一个用户名"
        style="margin-top: 8px"
      />
    </el-form-item>

    <!-- 密码字典 -->
    <el-form-item label="密码字典" prop="password_dict">
      <el-radio-group v-model="passwordType" @change="handlePasswordTypeChange">
        <el-radio value="select">选择已有字典</el-radio>
        <el-radio value="upload">上传新字典</el-radio>
        <el-radio value="manual">手动输入</el-radio>
      </el-radio-group>

      <!-- 选择已有字典 -->
      <el-select
        v-if="passwordType === 'select'"
        v-model="formData.password_dict_id"
        placeholder="请选择密码字典"
        style="width: 100%; margin-top: 8px"
      >
        <el-option
          v-for="dict in passwordDictionaries"
          :key="dict.id"
          :label="dict.name"
          :value="dict.id"
        />
      </el-select>

      <!-- 上传字典 -->
      <el-upload
        v-if="passwordType === 'upload'"
        ref="passwordUploadRef"
        :auto-upload="false"
        :limit="1"
        accept=".txt"
        :on-change="handlePasswordFileChange"
        style="margin-top: 8px"
      >
        <el-button type="primary">选择文件</el-button>
        <template #tip>
          <div class="el-upload__tip">支持 .txt 格式，每行一个密码</div>
        </template>
      </el-upload>

      <!-- 手动输入 -->
      <el-input
        v-if="passwordType === 'manual'"
        v-model="formData.password_list"
        type="textarea"
        :rows="4"
        placeholder="每行输入一个密码"
        style="margin-top: 8px"
      />
    </el-form-item>

    <!-- 任务选项 -->
    <el-divider content-position="left">任务选项</el-divider>

    <el-row :gutter="20">
      <el-col :span="8">
        <el-form-item label="线程数">
          <el-input-number v-model="formData.threads" :min="1" :max="10" />
        </el-form-item>
      </el-col>
      <el-col :span="8">
        <el-form-item label="请求延迟">
          <el-input-number
            v-model="formData.delay"
            :min="0"
            :max="10000"
            :step="100"
          />
          <span class="input-suffix">ms</span>
        </el-form-item>
      </el-col>
      <el-col :span="8">
        <el-form-item label="随机抖动">
          <el-input-number
            v-model="formData.jitter"
            :min="0"
            :max="5000"
            :step="100"
          />
          <span class="input-suffix">ms</span>
        </el-form-item>
      </el-col>
    </el-row>

    <el-form-item>
      <el-checkbox v-model="formData.stop_on_success">发现弱口令后停止</el-checkbox>
      <el-checkbox v-model="formData.enable_captcha">启用验证码识别</el-checkbox>
      <el-checkbox v-model="formData.show_browser">显示浏览器界面</el-checkbox>
    </el-form-item>

    <!-- 操作按钮 -->
    <el-form-item>
      <el-button @click="handleCancel">取消</el-button>
      <el-button type="primary" @click="handleSubmit" :loading="loading">
        创建任务
      </el-button>
    </el-form-item>
  </el-form>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { createTask } from '@/api/task'
import { getDictionaryList } from '@/api/dictionary'

const router = useRouter()
const emit = defineEmits(['success'])

const formRef = ref(null)
const loading = ref(false)

// URL协议前缀
const urlProtocol = ref('https://')

// 字典类型
const usernameType = ref('select')
const passwordType = ref('select')

// 字典文件
const usernameFile = ref(null)
const passwordFile = ref(null)

// 字典列表
const usernameDictionaries = ref([])
const passwordDictionaries = ref([])

// 表单数据
const formData = reactive({
  target_url: '',
  name: '',
  username_dict_id: null,
  password_dict_id: null,
  username_list: '',
  password_list: '',
  threads: 5,
  delay: 0,
  jitter: 0,
  stop_on_success: true,
  enable_captcha: true,
  show_browser: false
})

// 表单验证规则
const rules = {
  target_url: [
    { required: true, message: '请输入目标URL', trigger: 'blur' }
  ]
}

// 处理URL变化
const fullUrl = computed({
  get: () => {
    const url = formData.target_url
    if (url.startsWith('http://') || url.startsWith('https://')) {
      return url
    }
    return urlProtocol.value + url
  },
  set: (val) => {
    formData.target_url = val
  }
})

// 用户名字典类型变化
const handleUsernameTypeChange = () => {
  formData.username_dict_id = null
  formData.username_list = ''
  usernameFile.value = null
}

// 密码字典类型变化
const handlePasswordTypeChange = () => {
  formData.password_dict_id = null
  formData.password_list = ''
  passwordFile.value = null
}

// 用户名文件选择
const handleUsernameFileChange = (file) => {
  usernameFile.value = file.raw
}

// 密码文件选择
const handlePasswordFileChange = (file) => {
  passwordFile.value = file.raw
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
  } catch (error) {
    return
  }

  // 验证字典配置
  if (usernameType.value === 'select' && !formData.username_dict_id) {
    ElMessage.warning('请选择用户名字典，或切换到手动输入模式')
    return
  }
  if (passwordType.value === 'select' && !formData.password_dict_id) {
    ElMessage.warning('请选择密码字典，或切换到手动输入模式')
    return
  }
  if (usernameType.value === 'manual' && !formData.username_list?.trim()) {
    ElMessage.warning('请输入用户名')
    return
  }
  if (passwordType.value === 'manual' && !formData.password_list?.trim()) {
    ElMessage.warning('请输入密码')
    return
  }

  loading.value = true

  try {
    // 构建请求数据
    const data = {
      target_url: fullUrl.value,
      name: formData.name || undefined,
      threads: formData.threads,
      delay: formData.delay,
      jitter: formData.jitter,
      stop_on_success: formData.stop_on_success,
      enable_captcha: formData.enable_captcha,
      show_browser: formData.show_browser
    }

    // 处理字典数据
    if (usernameType.value === 'select' && formData.username_dict_id) {
      data.username_dict_id = formData.username_dict_id
    } else if (usernameType.value === 'manual' && formData.username_list) {
      data.username_list = formData.username_list.split('\n').filter(s => s.trim())
    } else if (usernameType.value === 'upload' && usernameFile.value) {
      data.username_file = usernameFile.value
    }

    if (passwordType.value === 'select' && formData.password_dict_id) {
      data.password_dict_id = formData.password_dict_id
    } else if (passwordType.value === 'manual' && formData.password_list) {
      data.password_list = formData.password_list.split('\n').filter(s => s.trim())
    } else if (passwordType.value === 'upload' && passwordFile.value) {
      data.password_file = passwordFile.value
    }

    console.log('Submitting task data:', data)
    await createTask(data)
    ElMessage.success('任务创建成功')
    emit('success')
    router.push('/task/list')
  } catch (error) {
    console.error('创建失败:', error)
  } finally {
    loading.value = false
  }
}

// 取消
const handleCancel = () => {
  router.back()
}

// 加载字典列表
const loadDictionaries = async () => {
  try {
    console.log('[TaskForm] Loading dictionaries...')
    const data = await getDictionaryList()
    console.log('[TaskForm] getDictionaryList returned:', JSON.stringify(data))
    const list = data.items || data || []
    console.log('[TaskForm] list:', JSON.stringify(list))
    usernameDictionaries.value = list.filter(d => d.type === 'username')
    passwordDictionaries.value = list.filter(d => d.type === 'password')
    console.log('[TaskForm] username dicts:', usernameDictionaries.value.length, 'password dicts:', passwordDictionaries.value.length)
  } catch (error) {
    console.error('加载字典失败:', error)
  }
}

onMounted(() => {
  loadDictionaries()
})
</script>

<style lang="scss" scoped>
.task-form {
  max-width: 800px;
  margin: 0 auto;
}

.input-suffix {
  margin-left: 8px;
  color: #909399;
}
</style>