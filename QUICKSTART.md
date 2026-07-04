# 🚀 BruteForceAI 快速入门

## 系统要求

- **Python**: 3.8 或更高版本
- **Node.js**: 16 或更高版本（用于前端）
- **操作系统**: Windows, macOS, 或 Linux

## 1. 克隆项目

```bash
git clone https://github.com/robe1t/BruteForceAI.git
cd BruteForceAI
```

## 2. 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
playwright install chromium
```

## 3. 安装前端依赖

```bash
cd ../frontend
npm install
```

## 4. 启动应用

```bash
# 返回项目根目录
cd ..
python start.py
```

这将启动：
- 后端服务: http://localhost:5000
- 前端界面: http://localhost:3000

## 5. 开始使用

在浏览器中打开 http://localhost:3000

### 主要功能模块

- 📊 **仪表板 (Dashboard)** - 查看任务概览和统计信息
- 📋 **任务管理 (Tasks)** - 创建和管理攻击任务
- 📖 **字典管理 (Dictionary)** - 管理用户名和密码列表
- 📈 **报告 (Reports)** - 查看详细的分析和结果
- ⚙️ **配置 (Config)** - 配置 LLM 提供商和设置

### 使用流程

1. **配置 LLM 提供商** (首次使用)
   - 进入 "Config" 页面
   - 选择并配置您喜欢的 LLM 提供商 (Ollama, OpenAI, Anthropic 等)

2. **准备字典**
   - 在 "Dictionary" 页面导入或创建用户名和密码列表

3. **创建任务**
   - 进入 "Tasks" 页面
   - 点击 "Create Task"
   - 填写目标 URL 和选择字典
   - 配置攻击参数
   - 启动任务

4. **监控任务**
   - 实时查看任务进度
   - 查看尝试详情
   - 查看成功的凭证

5. **查看报告**
   - 在任务完成后查看详细报告
   - 导出结果

## 命令行使用 (可选)

如果您更喜欢使用命令行：

```bash
# 分析表单
cd backend
python BruteForceAI.py analyze --urls targets.txt --llm-provider ollama

# 执行攻击
python BruteForceAI.py attack --urls targets.txt --usernames users.txt --passwords passwords.txt --threads 10
```

## 故障排除

### 问题: 后端启动失败
- 检查端口 5000 是否被占用
- 确保所有 Python 依赖已正确安装

### 问题: 前端无法访问后端
- 确认后端正在运行
- 检查浏览器控制台的网络请求

### 问题: Playwright 浏览器未安装
```bash
playwright install chromium
```

## 下一步

- 查看完整的 [README.md](README.md) 了解详细功能
- 查看 [API 文档](backend/API.md) 了解后端 API

---

**⚠️ 免责声明**: 此工具仅用于授权测试和教育目的。使用者需对其使用负责。
