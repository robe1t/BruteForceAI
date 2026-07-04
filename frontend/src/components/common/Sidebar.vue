<template>
  <aside class="sidebar">
    <el-menu
      :default-active="activeMenu"
      :collapse="isCollapse"
      class="sidebar-menu"
      @select="handleSelect"
    >
      <el-menu-item index="/">
        <el-icon><DataBoard /></el-icon>
        <template #title>仪表盘</template>
      </el-menu-item>

      <el-sub-menu index="task">
        <template #title>
          <el-icon><List /></el-icon>
          <span>任务管理</span>
        </template>
        <el-menu-item index="/task/create">创建任务</el-menu-item>
        <el-menu-item index="/task/list">任务列表</el-menu-item>
      </el-sub-menu>

      <el-menu-item index="/config">
        <el-icon><Setting /></el-icon>
        <template #title>系统配置</template>
      </el-menu-item>

      <el-menu-item index="/dictionary">
        <el-icon><Document /></el-icon>
        <template #title>字典管理</template>
      </el-menu-item>
    </el-menu>
  </aside>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const isCollapse = ref(false)

// 当前激活的菜单
const activeMenu = computed(() => {
  const { path } = route
  return path
})

// 菜单选择处理
const handleSelect = (index) => {
  router.push(index)
}
</script>

<style lang="scss" scoped>
.sidebar {
  width: 200px;
  min-height: calc(100vh - 60px);
  background: #fff;
  border-right: 1px solid #ebeef5;
}

.sidebar-menu {
  border-right: none;
  height: 100%;
}
</style>