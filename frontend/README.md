# 智能爆破安全审计系统 - 前端

## 技术栈

- Vue 3.4 + Composition API
- Vite 5
- Element Plus 2.6
- ECharts 5.5
- Socket.IO Client 4.7
- Pinia 2.1
- Axios 1.6

## 安装依赖

```bash
cd frontend
npm install
```

## 开发模式

```bash
npm run dev
```

访问 http://localhost:3000

## 生产构建

```bash
npm run build
```

## 项目结构

```
frontend/
├── public/             # 静态资源
├── src/
│   ├── api/           # API 请求封装
│   ├── components/    # 通用组件
│   │   ├── common/    # 公共组件
│   │   ├── config/    # 配置相关组件
│   │   ├── report/    # 报告相关组件
│   │   └── task/      # 任务相关组件
│   ├── router/        # 路由配置
│   ├── store/         # Pinia 状态管理
│   ├── styles/        # 全局样式
│   ├── utils/         # 工具函数
│   ├── views/         # 页面组件
│   ├── App.vue        # 根组件
│   └── main.js        # 入口文件
├── index.html
├── package.json
├── vite.config.js
└── .env.development
```

## 页面路由

| 路由 | 页面 | 描述 |
|------|------|------|
| / | Dashboard | 仪表盘 |
| /task/create | TaskCreate | 创建任务 |
| /task/list | TaskList | 任务列表 |
| /task/:id | TaskDetail | 任务详情 |
| /report/:id | Report | 安全报告 |
| /config | Config | 系统配置 |
| /dictionary | Dictionary | 字典管理 |

## 后端接口

后端服务地址: http://localhost:5000
- RESTful API: /api/v1/*
- WebSocket: ws://localhost:5000