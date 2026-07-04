<template>
  <div class="app-container">
    <Navbar />
    <main class="main-content">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
    <Footer />
  </div>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'
import Navbar from '@/components/common/Navbar.vue'
import Footer from '@/components/common/Footer.vue'
import websocket from '@/utils/websocket'

onMounted(() => {
  // 应用启动时连接WebSocket
  websocket.connect()
})

onUnmounted(() => {
  // 应用销毁时断开WebSocket
  websocket.disconnect()
})
</script>

<style lang="scss">
.app-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.main-content {
  flex: 1;
  padding: 20px;
  background-color: #f5f7fa;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>