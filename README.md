# 🤖 BruteForceAI - AI-Powered Login Brute Force Tool

<div align="center">

![BruteForceAI Banner](https://img.shields.io/badge/BruteForceAI-v1.0.0-red?style=for-the-badge&logo=security&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-Non--Commercial-orange?style=for-the-badge)
![AI Powered](https://img.shields.io/badge/AI-Powered-green?style=for-the-badge&logo=openai&logoColor=white)
![GitHub repo stars](https://img.shields.io/github/stars/robe1t/BruteForceAI?style=social)
![GitHub repo forks](https://img.shields.io/github/forks/robe1t/BruteForceAI?style=social)

[English](#english) | [中文](#中文)
</div>

---

## English

**Advanced LLM-powered brute-force tool combining AI intelligence with automated login attacks**

[Features](#-features) • [Quick Start](#-quick-start) • [Installation](#-installation) • [Usage](#-usage) • [Examples](#-examples) • [Configuration](#️-configuration-options) • [License](#-license)

</div>

---

## 🎯 About

BruteForceAI is an advanced penetration testing tool that revolutionizes traditional brute-force attacks by integrating Large Language Models (LLM) for intelligent form analysis. The tool automatically identifies login form selectors using AI, then executes sophisticated multi-threaded attacks with human-like behavior patterns.

### 🧠 LLM-Powered Form Analysis
- **Stage 1 (AI Analysis)**: LLM analyzes HTML content to identify login form elements and selectors
- **Stage 2 (Smart Attack)**: Executes intelligent brute-force attacks using AI-discovered selectors

### 🚀 Advanced Attack Features
- **Multi-threaded execution** with synchronized delays
- **Bruteforce & Password Spray** attack modes
- **Human-like timing** with jitter and randomization
- **User-Agent rotation** for better evasion
- **Webhook notifications** (Discord, Slack, Teams, Telegram)
- **Comprehensive logging** with SQLite database

---

## 🚀 Quick Start

Get BruteForceAI up and running in minutes with the web interface:

### 1. Install Dependencies

```bash
# Backend dependencies
cd backend
pip install -r requirements.txt
playwright install chromium

# Frontend dependencies
cd ../frontend
npm install
```

### 2. Launch the Application

```bash
# From the project root
python start.py
```

This will start:
- Backend server at `http://localhost:5000`
- Frontend interface at `http://localhost:3000`

### 3. Access the Web UI

Open your browser and navigate to `http://localhost:3000` to use the graphical interface!

---

## ✨ Features

### 🖥️ **Modern Web Interface**
- Beautiful Vue.js-based dashboard
- Real-time WebSocket updates
- Task management and monitoring
- Dictionary management
- Comprehensive reports and analytics
- Configuration panel for LLM providers

### 🔍 **Intelligent Analysis**
- LLM-powered form selector identification (Ollama/Groq)
- Automatic retry with feedback learning
- DOM change detection for success validation
- Smart HTML content extraction

### ⚡ **Advanced Attacks**
- **Bruteforce Mode**: Try all username/password combinations
- **Password Spray Mode**: Test each password against all usernames
- Multi-threaded execution (1-100+ threads)
- Synchronized delays between attempts for same user

### 🎭 **Evasion Techniques**
- Random User-Agent rotation
- Configurable delays with jitter
- Human-like timing patterns
- Proxy support
- Browser visibility control

### 📊 **Monitoring & Notifications**
- Real-time webhook notifications on success
- Comprehensive SQLite logging
- Verbose timestamped output
- Success exit after first valid credentials
- Skip existing attempts (duplicate prevention)

### 🛠️ **Operational Features**
- Output capture to files
- Colorful terminal interface
- Network error retry mechanism
- Force retry existing attempts
- Database management tools
- **Automatic update checking** from mordavid.com

---

## 🔧 Installation

### Prerequisites
```bash
# Python 3.8 or higher
python --version

# Install Playwright browsers
playwright install chromium
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

**Required packages:**
- `playwright` - Browser automation
- `requests` - HTTP requests
- `PyYAML` - YAML parsing for update checks

### LLM Setup

#### Option 1: Ollama (Local)
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull recommended model
ollama pull llama3.2:3b
```

#### Option 2: Groq (Cloud)
1. Get API key from [Groq Console](https://console.groq.com/)
2. Use with `--llm-provider groq --llm-api-key YOUR_KEY`

### 🧠 Model Selection & Performance

#### Recommended Models by Provider

**Ollama (Local):**
- `llama3.2:3b` - Default, good balance of speed and quality
- `llama3.2:1b` - Fastest, smaller model for quick analysis
- `qwen2.5:3b` - Alternative with good performance

**Groq (Cloud):**
- `llama-3.3-70b-versatile` - **Default & Best** - Latest model with superior quality (1 attempt)
- `llama3-70b-8192` - Fast and reliable alternative (1 attempt)
- `gemma2-9b-it` - Lightweight option, good for simple forms (1 attempt)
- `llama-3.1-8b-instant` - ⚠️ Not recommended (rate limiting issues, 3+ attempts)

#### Performance Tips
```bash
# Best quality (recommended for complex forms)
python main.py analyze --urls targets.txt --llm-provider groq --llm-model llama-3.3-70b-versatile --llm-api-key YOUR_KEY

# Fast and reliable
python main.py analyze --urls targets.txt --llm-provider groq --llm-model llama3-70b-8192 --llm-api-key YOUR_KEY

# Lightweight for simple forms
python main.py analyze --urls targets.txt --llm-provider groq --llm-model gemma2-9b-it --llm-api-key YOUR_KEY

# Local processing (no API key needed)
python main.py analyze --urls targets.txt --llm-provider ollama --llm-model llama3.2:3b
```

---

## 📖 Usage

### Web Interface (Recommended)

The easiest way to use BruteForceAI is through the modern web interface:

```bash
# Start the web application
python start.py
```

Then open `http://localhost:3000` in your browser to access:
- Dashboard - Overview of tasks and statistics
- Tasks - Create, monitor, and manage attack tasks
- Dictionary - Manage username and password lists
- Reports - View detailed analysis and results
- Config - Configure LLM providers and settings

### Command Line Interface (CLI)

#### Stage 1: Analyze Login Forms
```bash
python main.py analyze --urls urls.txt --llm-provider ollama
```

#### Stage 2: Execute Attack
```bash
python main.py attack --urls urls.txt --usernames users.txt --passwords passwords.txt --threads 10
```

### Command Structure
```bash
python main.py <command> [options]
```

#### Available Commands
- `analyze` - Analyze login forms with LLM
- `attack` - Execute brute-force attacks
- `clean-db` - Clean database tables
- `check-updates` - Check for software updates

---

## 🎯 Examples

### 1. Complete Workflow
```bash
# Step 1: Analyze forms
python main.py analyze --urls targets.txt --llm-provider ollama --llm-model llama3.2:3b

# Step 2: Attack with 20 threads
python main.py attack --urls targets.txt --usernames users.txt --passwords passwords.txt --threads 20 --delay 5 --jitter 2
```

### 2. Advanced Attack Configuration
```bash
python main.py attack \
  --urls targets.txt \
  --usernames users.txt \
  --passwords passwords.txt \
  --mode passwordspray \
  --threads 15 \
  --delay 10 \
  --jitter 3 \
  --success-exit \
  --user-agents user_agents.txt \
  --verbose \
  --output results.txt
```

### 3. With Webhook Notifications
```bash
python main.py attack \
  --urls targets.txt \
  --usernames users.txt \
  --passwords passwords.txt \
  --discord-webhook "https://discord.com/api/webhooks/..." \
  --slack-webhook "https://hooks.slack.com/services/..." \
  --threads 10
```

### 4. Browser Debugging
```bash
python main.py analyze \
  --urls targets.txt \
  --show-browser \
  --browser-wait 5 \
  --debug \
  --llm-provider ollama
```

### 5. Check for Updates
```bash
# Check for software updates
python main.py check-updates

# Check with output to file
python main.py check-updates --output update_check.txt
```

### Manual Check (Detailed)
```bash
# Check for updates manually (same as automatic but can save to file)
python main.py check-updates

# Check with output to file
python main.py check-updates --output update_check.txt
```

### Skip Version Check
```bash
# Skip version check completely for faster startup
python main.py analyze --urls targets.txt --skip-version-check
python main.py attack --urls targets.txt --usernames users.txt --passwords passwords.txt --skip-version-check

# Also works as global flag (before subcommand)
python main.py --skip-version-check analyze --urls targets.txt
```

---

## ⚙️ Configuration Options

### Analysis Options
| Parameter | Description | Default |
|-----------|-------------|---------|
| `--llm-provider` | LLM provider (ollama/groq) | ollama |
| `--llm-model` | Model name | llama3.2:3b (ollama), llama-3.3-70b-versatile (groq) |
| `--llm-api-key` | API key for Groq | None |
| `--selector-retry` | Retry attempts for selectors | 10 |
| `--force-reanalyze` | Force re-analysis | False |

### Attack Options
| Parameter | Description | Default |
|-----------|-------------|---------|
| `--mode` | Attack mode (bruteforce/passwordspray) | bruteforce |
| `--threads` | Number of threads | 1 |
| `--delay` | Delay between attempts (seconds) | 0 |
| `--jitter` | Random jitter (seconds) | 0 |
| `--success-exit` | Stop after first success | False |
| `--force-retry` | Retry existing attempts | False |

### Detection Options
| Parameter | Description | Default |
|-----------|-------------|---------|
| `--dom-threshold` | DOM difference threshold | 100 |
| `--retry-attempts` | Network retry attempts | 3 |

### Evasion Options
| Parameter | Description | Default |
|-----------|-------------|---------|
| `--user-agents` | User-Agent file | None |
| `--proxy` | Proxy server | None |
| `--show-browser` | Show browser window | False |
| `--browser-wait` | Wait time when visible | 0 |

### Output Options
| Parameter | Description | Default |
|-----------|-------------|---------|
| `--verbose` | Detailed timestamps | False |
| `--debug` | Debug information | False |
| `--output` | Save output to file | None |
| `--no-color` | Disable colors | False |

### Webhook Options
| Parameter | Description |
|-----------|-------------|
| `--discord-webhook` | Discord webhook URL |
| `--slack-webhook` | Slack webhook URL |
| `--teams-webhook` | Teams webhook URL |
| `--telegram-webhook` | Telegram bot token |
| `--telegram-chat-id` | Telegram chat ID |

---

## 🗄️ Database Schema

BruteForceAI uses SQLite database (`bruteforce.db`) with two main tables:

### form_analysis
Stores LLM analysis results for each URL.

### brute_force_attempts  
Logs all attack attempts with results and metadata.

### Database Management
```bash
# Clean all data
python main.py clean-db

# View database
sqlite3 bruteforce.db
.tables
.schema
```

---

## 🔔 Webhook Integration

### Discord Setup
1. Create webhook in Discord server settings
2. Use webhook URL with `--discord-webhook`

### Slack Setup
1. Create Slack app with incoming webhooks
2. Use webhook URL with `--slack-webhook`

### Teams Setup
1. Add "Incoming Webhook" connector to Teams channel
2. Use webhook URL with `--teams-webhook`

### Telegram Setup
1. Create bot with @BotFather
2. Get bot token and chat ID
3. Use `--telegram-webhook TOKEN --telegram-chat-id CHAT_ID`

---

## ⚠️ Legal Disclaimer

**FOR EDUCATIONAL AND AUTHORIZED TESTING ONLY**

This tool is designed for:
- ✅ Authorized penetration testing
- ✅ Security research and education
- ✅ Testing your own applications
- ✅ Bug bounty programs with proper scope

**DO NOT USE FOR:**
- ❌ Unauthorized access to systems
- ❌ Illegal activities
- ❌ Attacking systems without permission

Users are responsible for complying with all applicable laws and regulations. The author assumes no liability for misuse of this tool.

---

## 📋 Changelog

### v1.0.2
- 📝 Remove logo from README
- 📝 Add Chinese translation of README
- 🗑️ Remove test files from git
- 📝 Update .gitignore to exclude test files and logo

### v1.0.1
- 📝 Update README to remove original author references
- 📝 Add proper badges pointing to current repository
- 📝 Add QUICKSTART.md for easy onboarding
- 📝 Add web interface documentation

### v1.0.0
- ✨ Initial release
- 🧠 LLM-powered form analysis
- ⚡ Multi-threaded attacks
- 🎭 Advanced evasion techniques
- 🔔 Webhook notifications
- 📊 Comprehensive logging

---

## 📄 License

This project is licensed under the **Non-Commercial License**.

### Terms Summary:
- ✅ **Permitted**: Personal use, education, research, authorized testing
- ❌ **Prohibited**: Commercial use, redistribution for profit, unauthorized attacks
- 📋 **Requirements**: Attribution, same license for derivatives

See the [LICENSE.md](LICENSE.md) file for complete terms and conditions.

---

## 🙏 Acknowledgments

- **Playwright Team** - For the excellent browser automation framework
- **Ollama Project** - For making local LLM deployment accessible
- **Groq** - For high-performance LLM inference
- **Security Community** - For continuous feedback and improvements

---

<div align="center">

**⭐ Star this repository if you find it useful!**

**Made with ❤️**

</div>

---

## 中文

# 🤖 BruteForceAI - AI 驱动的登录暴力破解工具

<div align="center">

**结合人工智能和自动化登录攻击的高级 LLM 驱动暴力破解工具**

[功能特性](#-功能特性) • [快速开始](#-快速开始) • [安装](#-安装) • [使用](#-使用) • [示例](#-示例) • [配置](#️-配置选项) • [许可证](#-许可证)

</div>

---

## 🎯 关于

BruteForceAI 是一款高级渗透测试工具，通过集成大型语言模型（LLM）进行智能表单分析，彻底革新了传统暴力破解方式。该工具使用 AI 自动识别登录表单选择器，然后执行具有类人行为模式的复杂多线程攻击。

### 🧠 LLM 驱动的表单分析
- **第一阶段（AI 分析）**：LLM 分析 HTML 内容以识别登录表单元素和选择器
- **第二阶段（智能攻击）**：使用 AI 发现的选择器执行智能暴力破解攻击

### 🚀 高级攻击特性
- 同步延迟的多线程执行
- 暴力破解和密码喷洒攻击模式
- 具有抖动和随机性的类人时序
- 用户代理轮换以更好地规避检测
- Webhook 通知（Discord、Slack、Teams、Telegram）
- 完整的 SQLite 数据库记录

---

## 🚀 快速开始

使用 Web 界面让 BruteForceAI 快速运行起来：

### 1. 安装依赖

```bash
# 后端依赖
cd backend
pip install -r requirements.txt
playwright install chromium

# 前端依赖
cd ../frontend
npm install
```

### 2. 启动应用

```bash
# 从项目根目录
python start.py
```

这将启动：
- 后端服务：http://localhost:5000
- 前端界面：http://localhost:3000

### 3. 访问 Web UI

在浏览器中打开 http://localhost:3000 使用图形界面！

---

## ✨ 功能特性

### 🖥️ 现代化 Web 界面
- 美观的基于 Vue.js 的仪表板
- 实时 WebSocket 更新
- 任务管理和监控
- 字典管理
- 全面的报告和分析
- LLM 提供商配置面板

### 🔍 智能分析
- LLM 驱动的表单选择器识别（Ollama/Groq）
- 带反馈学习的自动重试
- 用于成功验证的 DOM 变化检测
- 智能 HTML 内容提取

### ⚡ 高级攻击
- **暴力破解模式**：尝试所有用户名/密码组合
- **密码喷洒模式**：针对所有用户名测试每个密码
- 多线程执行（1-100+ 线程）
- 同一用户尝试之间的同步延迟

### 🎭 规避技术
- 随机用户代理轮换
- 可配置的延迟和抖动
- 类人时序模式
- 代理支持
- 浏览器可见性控制

### 📊 监控和通知
- 成功时的实时 Webhook 通知
- 完整的 SQLite 日志记录
- 详细的时间戳输出
- 首次有效凭证后成功退出
- 跳过现有尝试（防止重复）

### 🛠️ 操作特性
- 输出保存到文件
- 彩色终端界面
- 网络错误重试机制
- 强制重试现有尝试
- 数据库管理工具

---

## 📖 使用

### Web 界面（推荐）

使用 BruteForceAI 最简单的方式是通过现代化 Web 界面：

```bash
# 启动 Web 应用
python start.py
```

然后在浏览器中打开 http://localhost:3000 访问：
- 仪表板 - 任务和统计概览
- 任务 - 创建、监控和管理攻击任务
- 字典 - 管理用户名和密码列表
- 报告 - 查看详细的分析和结果
- 配置 - 配置 LLM 提供商和设置

### 命令行界面（CLI）

#### 第一阶段：分析登录表单
```bash
python main.py analyze --urls urls.txt --llm-provider ollama
```

#### 第二阶段：执行攻击
```bash
python main.py attack --urls urls.txt --usernames users.txt --passwords passwords.txt --threads 10
```

### 命令结构
```bash
python main.py <command> [options]
```

#### 可用命令
- `analyze` - 使用 LLM 分析登录表单
- `attack` - 执行暴力破解攻击
- `clean-db` - 清理数据库表

---

## 🎯 示例

### 1. 完整工作流
```bash
# 第一步：分析表单
python main.py analyze --urls targets.txt --llm-provider ollama --llm-model llama3.2:3b

# 第二步：使用 20 个线程攻击
python main.py attack --urls targets.txt --usernames users.txt --passwords passwords.txt --threads 20 --delay 5 --jitter 2
```

### 2. 高级攻击配置
```bash
python main.py attack \
  --urls targets.txt \
  --usernames users.txt \
  --passwords passwords.txt \
  --mode passwordspray \
  --threads 15 \
  --delay 10 \
  --jitter 3 \
  --success-exit \
  --user-agents user_agents.txt \
  --verbose \
  --output results.txt
```

### 3. 带 Webhook 通知
```bash
python main.py attack \
  --urls targets.txt \
  --usernames users.txt \
  --passwords passwords.txt \
  --discord-webhook "https://discord.com/api/webhooks/..." \
  --slack-webhook "https://hooks.slack.com/services/..." \
  --threads 10
```

### 4. 浏览器调试
```bash
python main.py analyze \
  --urls targets.txt \
  --show-browser \
  --browser-wait 5 \
  --debug \
  --llm-provider ollama
```

### 跳过版本检查
```bash
# 完全跳过版本检查以加快启动速度
python main.py analyze --urls targets.txt --skip-version-check
python main.py attack --urls targets.txt --usernames users.txt --passwords passwords.txt --skip-version-check

# 也可以作为全局标志使用（在子命令之前）
python main.py --skip-version-check analyze --urls targets.txt
```

---

## ⚙️ 配置选项

### 分析选项
| 参数 | 描述 | 默认值 |
|------|------|--------|
| `--llm-provider` | LLM 提供商（ollama/groq） | ollama |
| `--llm-model` | 模型名称 | llama3.2:3b（ollama），llama-3.3-70b-versatile（groq） |
| `--llm-api-key` | Groq 的 API 密钥 | 无 |
| `--selector-retry` | 选择器重试次数 | 10 |
| `--force-reanalyze` | 强制重新分析 | False |

### 攻击选项
| 参数 | 描述 | 默认值 |
|------|------|--------|
| `--mode` | 攻击模式（bruteforce/passwordspray） | bruteforce |
| `--threads` | 线程数 | 1 |
| `--delay` | 尝试之间的延迟（秒） | 0 |
| `--jitter` | 随机抖动（秒） | 0 |
| `--success-exit` | 首次成功后退出 | False |
| `--force-retry` | 重试现有尝试 | False |

### 检测选项
| 参数 | 描述 | 默认值 |
|------|------|--------|
| `--dom-threshold` | DOM 差异阈值 | 100 |
| `--retry-attempts` | 网络重试次数 | 3 |

### 规避选项
| 参数 | 描述 | 默认值 |
|------|------|--------|
| `--user-agents` | 用户代理文件 | 无 |
| `--proxy` | 代理服务器 | 无 |
| `--show-browser` | 显示浏览器窗口 | False |
| `--browser-wait` | 可见时的等待时间 | 0 |

### 输出选项
| 参数 | 描述 | 默认值 |
|------|------|--------|
| `--verbose` | 详细时间戳 | False |
| `--debug` | 调试信息 | False |
| `--output` | 保存输出到文件 | 无 |
| `--no-color` | 禁用颜色 | False |

### Webhook 选项
| 参数 | 描述 |
|------|------|
| `--discord-webhook` | Discord Webhook URL |
| `--slack-webhook` | Slack Webhook URL |
| `--teams-webhook` | Teams Webhook URL |
| `--telegram-webhook` | Telegram 机器人令牌 |
| `--telegram-chat-id` | Telegram 聊天 ID |

---

## 🗄️ 数据库架构

BruteForceAI 使用 SQLite 数据库（`bruteforce.db`），包含两个主要表：

### form_analysis
存储每个 URL 的 LLM 分析结果。

### brute_force_attempts
记录所有攻击尝试及其结果和元数据。

### 数据库管理
```bash
# 清理所有数据
python main.py clean-db

# 查看数据库
sqlite3 bruteforce.db
.tables
.schema
```

---

## 🔔 Webhook 集成

### Discord 设置
1. 在 Discord 服务器设置中创建 Webhook
2. 使用带 `--discord-webhook` 的 Webhook URL

### Slack 设置
1. 创建带传入 Webhook 的 Slack 应用
2. 使用带 `--slack-webhook` 的 Webhook URL

### Teams 设置
1. 向 Teams 频道添加 "传入 Webhook" 连接器
2. 使用带 `--teams-webhook` 的 Webhook URL

### Telegram 设置
1. 使用 @BotFather 创建机器人
2. 获取机器人令牌和聊天 ID
3. 使用 `--telegram-webhook TOKEN --telegram-chat-id CHAT_ID`

---

## ⚠️ 法律免责声明

**仅供教育和授权测试使用**

本工具设计用于：
- ✅ 授权的渗透测试
- ✅ 安全研究和教育
- ✅ 测试您自己的应用
- ✅ 有适当范围的漏洞赏金计划

**禁止使用于：**
- ❌ 未经授权访问系统
- ❌ 非法活动
- ❌ 未经许可攻击系统

用户有责任遵守所有适用法律法规。作者不对工具的滥用承担责任。

---

## 📋 更新日志

### v1.0.2
- 📝 从 README 中移除 Logo
- 📝 添加 README 中文版翻译
- 🗑️ 从 git 中移除测试文件
- 📝 更新 .gitignore 排除测试文件和 logo

### v1.0.1
- 📝 更新 README 移除原作者引用
- 📝 添加指向当前仓库的正确徽章
- 📝 添加 QUICKSTART.md 便于快速上手
- 📝 添加 Web 界面文档

### v1.0.0
- ✨ 初始发布
- 🧠 LLM 驱动的表单分析
- ⚡ 多线程攻击
- 🎭 高级规避技术
- 🔔 Webhook 通知
- 📊 全面的日志记录

---

## 📄 许可证

本项目采用 **非商业许可证**。

### 条款摘要：
- ✅ **允许**：个人使用、教育、研究、授权测试
- ❌ **禁止**：商业使用、为盈利目的再分发、未经授权的攻击
- 📋 **要求**：注明来源、衍生作品使用相同许可证

查看 [LICENSE.md](LICENSE.md) 文件了解完整条款和条件。

---

## 🙏 致谢

- **Playwright 团队** - 出色的浏览器自动化框架
- **Ollama 项目** - 使本地 LLM 部署变得可访问
- **Groq** - 高性能 LLM 推理
- **安全社区** - 持续的反馈和改进

---

<div align="center">

**⭐ 如果这个仓库对你有用，请 Star！**

**用 ❤️ 制作**

</div> 
