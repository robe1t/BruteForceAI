# 智能爆破安全审计系统 - 后端

## 项目概述

基于 Flask + Playwright + SQLite 构建的智能登录安全审计系统后端服务。

## 技术栈

- **Python**: 3.10+
- **Web 框架**: Flask 3.0
- **实时通信**: Flask-SocketIO (threading 模式)
- **浏览器自动化**: Playwright
- **数据库**: SQLite
- **验证码识别**: ddddocr
- **LLM 支持**: OpenAI API / Anthropic API

## 项目结构

```
backend/
├── app/
│   ├── __init__.py          # Flask 应用工厂
│   ├── config.py            # 配置管理
│   │
│   ├── api/                  # RESTful API
│   │   ├── task.py          # 任务管理 API
│   │   ├── analyze.py       # 页面分析 API
│   │   ├── report.py        # 报告 API
│   │   ├── config_api.py    # 配置 API
│   │   ├── dictionary.py    # 字典 API
│   │   └── websocket.py     # WebSocket 处理
│   │
│   ├── core/                 # 核心业务模块
│   │   ├── browser_pool.py  # 浏览器复用池
│   │   ├── task_manager.py  # 任务管理器
│   │   ├── page_analyzer.py # 页面分析器
│   │   ├── attacker.py      # 爆破执行器
│   │   └── evaluator.py     # 安全评估器
│   │
│   ├── captcha/              # 验证码处理
│   │   ├── detector.py      # 验证码检测器
│   │   └── ocr_solver.py    # OCR 解决器
│   │
│   ├── llm/                  # LLM 服务
│   │   ├── base.py          # 抽象基类
│   │   ├── openai_compatible.py
│   │   └── anthropic.py
│   │
│   ├── database/             # 数据库
│   │   ├── db.py            # 数据库连接
│   │   └── models.py        # ORM 模型
│   │
│   └── utils/                # 工具函数
│       └── helpers.py
│
├── tests/                    # 测试
├── config/                   # 配置文件
├── data/                     # 数据存储
├── requirements.txt
├── run.py                    # 启动脚本
└── API.md                    # API 文档
```

## 快速开始

### 安装依赖

```bash
cd backend
pip install -r requirements.txt
playwright install chromium
```

### 启动服务

```bash
python run.py
```

### 启动选项

```bash
python run.py --host 0.0.0.0 --port 5000 --debug
```

## API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/tasks` | GET/POST | 任务列表/创建 |
| `/api/v1/tasks/<id>/start` | POST | 启动任务 |
| `/api/v1/tasks/<id>/stop` | POST | 停止任务 |
| `/api/v1/analyze` | POST | 分析页面 |
| `/api/v1/reports/<id>` | GET | 获取报告 |
| `/api/v1/config/providers` | GET/POST | 提供商管理 |
| `/api/v1/dictionaries` | GET/POST | 字典管理 |

## 数据库表

- `audit_tasks` - 审计任务
- `page_analyses` - 页面分析结果
- `test_results` - 测试结果
- `security_findings` - 安全发现
- `security_scores` - 安全评分
- `providers` - LLM 提供商配置
- `dictionaries` - 字典
- `system_config` - 系统配置

## WebSocket 事件

- `subscribe` - 订阅任务更新
- `task_progress` - 任务进度
- `credential_found` - 发现弱口令
- `task_completed` - 任务完成
- `log` - 日志输出

## 开发

### 运行测试

```bash
pytest tests/
```

### 代码规范

- Python 3.10+ 语法
- 使用 Type Hints
- 遵循 PEP 8 规范

## 许可证

MIT License