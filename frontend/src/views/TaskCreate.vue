<template>
  <div class="task-create page-container">
    <div class="page-header">
      <h1 class="page-title">创建审计任务</h1>
    </div>

    <TaskForm @success="handleSuccess" />
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import TaskForm from '@/components/task/TaskForm.vue'

const router = useRouter()

// 创建成功回调
const handleSuccess = () => {
  router.push('/task/list')
}
</script>

<style lang="scss" scoped>
.task-create {
  max-width: 900px;
  margin: 0 auto;
}
</style>