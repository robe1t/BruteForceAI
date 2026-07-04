<template>
  <div class="dictionary page-container">
    <div class="page-header">
      <h1 class="page-title">字典管理</h1>
      <el-button type="primary" @click="showUploadDialog">
        <el-icon><Upload /></el-icon>
        上传字典
      </el-button>
    </div>

    <!-- 字典列表 -->
    <div class="form-card">
      <el-table :data="dictionaries" v-loading="loading" stripe>
        <el-table-column prop="name" label="名称" min-width="150" />

        <el-table-column prop="type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="row.type === 'username' ? 'primary' : 'warning'" size="small">
              {{ row.type === 'username' ? '用户名' : '密码' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="count" label="条目数" width="120">
          <template #default="{ row }">
            {{ formatNumber(row.count || 0) }}
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handlePreview(row)">
              查看
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

      <el-empty v-if="!loading && dictionaries.length === 0" description="暂无字典" />
    </div>

    <!-- 字典内容预览 -->
    <div class="form-card" v-if="previewData.length > 0">
      <div class="card-title">
        <span>字典内容: {{ previewName }} (前{{ previewData.length }}条)</span>
        <el-button text size="small" @click="previewData = []">关闭</el-button>
      </div>
      <div class="preview-content">
        <div
          v-for="(item, index) in previewData"
          :key="index"
          class="preview-item"
        >
          {{ item }}
        </div>
      </div>
    </div>

    <!-- 上传对话框 -->
    <el-dialog
      v-model="uploadDialogVisible"
      title="上传字典"
      width="500px"
      destroy-on-close
    >
      <el-form ref="uploadFormRef" :model="uploadForm" :rules="uploadRules" label-width="80px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="uploadForm.name" placeholder="请输入字典名称" />
        </el-form-item>

        <el-form-item label="类型" prop="type">
          <el-radio-group v-model="uploadForm.type">
            <el-radio value="username">用户名</el-radio>
            <el-radio value="password">密码</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="文件" prop="file">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            accept=".txt"
            :on-change="handleFileChange"
            drag
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">
              拖拽文件到此处或 <em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">支持 .txt 格式，每行一条数据</div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="uploadDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleUpload" :loading="uploading">
          上传
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { getDictionaryList, uploadDictionary, deleteDictionary, previewDictionary } from '@/api/dictionary'
import { formatDateTime, formatNumber } from '@/utils/format'

const loading = ref(false)
const dictionaries = ref([])
const uploadDialogVisible = ref(false)
const uploading = ref(false)

const uploadFormRef = ref(null)
const uploadRef = ref(null)
const uploadFile = ref(null)

// 上传表单
const uploadForm = reactive({
  name: '',
  type: 'password',
  file: null
})

// 上传表单验证规则
const uploadRules = {
  name: [
    { required: true, message: '请输入字典名称', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择字典类型', trigger: 'change' }
  ]
}

// 预览数据
const previewName = ref('')
const previewData = ref([])

// 加载字典列表
const fetchDictionaries = async () => {
  loading.value = true
  try {
    const data = await getDictionaryList()
    dictionaries.value = (data.items || data || []).map(d => ({
      ...d,
      _deleting: false
    }))
  } catch (error) {
    console.error('获取字典列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 显示上传对话框
const showUploadDialog = () => {
  uploadForm.name = ''
  uploadForm.type = 'password'
  uploadForm.file = null
  uploadFile.value = null
  uploadDialogVisible.value = true
}

// 文件选择
const handleFileChange = (file) => {
  uploadFile.value = file.raw
  // 自动填充名称
  if (!uploadForm.name && file.name) {
    uploadForm.name = file.name.replace('.txt', '')
  }
}

// 上传字典
const handleUpload = async () => {
  if (!uploadFormRef.value) return

  try {
    await uploadFormRef.value.validate()
  } catch (error) {
    return
  }

  if (!uploadFile.value) {
    ElMessage.warning('请选择要上传的文件')
    return
  }

  uploading.value = true
  try {
    await uploadDictionary({
      name: uploadForm.name,
      type: uploadForm.type,
      file: uploadFile.value
    })
    ElMessage.success('上传成功')
    uploadDialogVisible.value = false
    fetchDictionaries()
  } catch (error) {
    console.error('上传失败:', error)
  } finally {
    uploading.value = false
  }
}

// 预览字典
const handlePreview = async (row) => {
  try {
    const data = await previewDictionary(row.id, 50)
    previewName.value = row.name
    previewData.value = data.items || data || []
  } catch (error) {
    console.error('获取预览失败:', error)
    ElMessage.error('获取字典内容失败')
  }
}

// 删除字典
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除此字典吗?', '提示', {
      type: 'warning'
    })

    row._deleting = true
    await deleteDictionary(row.id)
    ElMessage.success('删除成功')
    fetchDictionaries()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
    }
  } finally {
    row._deleting = false
  }
}

onMounted(() => {
  fetchDictionaries()
})
</script>

<style lang="scss" scoped>
.dictionary {
  .preview-content {
    max-height: 300px;
    overflow-y: auto;
    background: #f5f7fa;
    border-radius: 8px;
    padding: 16px;
    font-family: monospace;

    .preview-item {
      padding: 4px 0;
      color: #606266;
      border-bottom: 1px dashed #e4e7ed;

      &:last-child {
        border-bottom: none;
      }
    }
  }
}
</style>