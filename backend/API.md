# 智能爆破安全审计系统 - API 文档

## 基础信息

- **基础 URL**: `http://localhost:5000/api/v1`
- **响应格式**: JSON
- **字符编码**: UTF-8

## 通用响应格式

### 成功响应
```json
{
    "success": true,
    "data": { ... },
    "message": "操作成功"
}
```

### 错误响应
```json
{
    "success": false,
    "error": {
        "code": "ERROR_CODE",
        "message": "错误描述"
    }
}
```

## 错误码定义

| 错误码 | 说明 |
|--------|------|
| TASK_NOT_FOUND | 任务不存在 |
| TASK_ALREADY_RUNNING | 任务已在运行 |
| INVALID_URL | URL 格式无效 |
| PROVIDER_NOT_FOUND | 提供商不存在 |
| CAPTCHA_UNSUPPORTED | 不支持的验证码类型 |
| LLM_ERROR | LLM 调用错误 |
| BROWSER_ERROR | 浏览器错误 |

---

## 任务管理 API

### 创建任务

**POST** `/tasks`

创建新的安全审计任务。

**请求体**:
```json
{
    "url": "https://example.com/login",
    "name": "测试任务",
    "options": {
        "threads": 5,
        "delay": 1000,
        "jitter": 500,
        "stop_on_success": true,
        "enable_captcha": true,
        "show_browser": false,
        "username_dict_id": 1,
        "password_dict_id": 2
    }
}
```

**响应**:
```json
{
    "success": true,
    "data": {
        "id": 1,
        "task_id": "task_abc123def456",
        "name": "测试任务",
        "url": "https://example.com/login",
        "status": "pending",
        "created_at": "2024-01-01T12:00:00"
    }
}
```

### 获取任务列表

**GET** `/tasks`

**查询参数**:
- `status`: 按状态筛选 (pending, running, completed, failed, stopped)
- `page`: 页码 (默认: 1)
- `page_size`: 每页数量 (默认: 20)

**响应**:
```json
{
    "success": true,
    "data": {
        "items": [...],
        "total": 100,
        "page": 1,
        "page_size": 20
    }
}
```

### 获取任务详情

**GET** `/tasks/<task_id>`

**响应**:
```json
{
    "success": true,
    "data": {
        "task_id": "task_abc123def456",
        "name": "测试任务",
        "url": "https://example.com/login",
        "status": "completed",
        "analysis": {...},
        "credentials": [...]
    }
}
```

### 启动任务

**POST** `/tasks/<task_id>/start`

**响应**:
```json
{
    "success": true,
    "data": {
        "queue_position": 1
    }
}
```

### 停止任务

**POST** `/tasks/<task_id>/stop`

### 删除任务

**DELETE** `/tasks/<task_id>`

### 获取任务进度

**GET** `/tasks/<task_id>/progress`

---

## 页面分析 API

### 分析页面

**POST** `/analyze`

分析登录页面结构，识别选择器和验证码。

**请求体**:
```json
{
    "url": "https://example.com/login"
}
```

**响应**:
```json
{
    "success": true,
    "data": {
        "username_selector": "#username",
        "password_selector": "#password",
        "submit_selector": "button[type=\"submit\"]",
        "has_captcha": true,
        "captcha_type": "image",
        "captcha_selector": "#captcha_img",
        "captcha_input_selector": "#captcha_input",
        "failed_dom_length": 1234
    }
}
```

### 获取分析结果

**GET** `/analyze/<task_id>`

---

## 报告 API

### 获取测试报告

**GET** `/reports/<task_id>`

**响应**:
```json
{
    "success": true,
    "data": {
        "task_id": "task_abc123",
        "target_url": "https://example.com/login",
        "status": "completed",
        "score": 45,
        "score_details": {
            "weak_password": {"score": 20, "description": "发现5个弱口令"},
            "captcha": {"score": 60, "description": "验证码可被识别"},
            "lockout": {"score": 40, "description": "未检测到账户锁定策略"},
            "rate_limit": {"score": 30, "description": "未检测到请求频率限制"}
        },
        "credentials": [
            {"username": "admin", "password": "admin123"}
        ],
        "findings": [...],
        "recommendations": [...]
    }
}
```

### 导出报告

**GET** `/reports/<task_id>/export?format=html`

**查询参数**:
- `format`: 导出格式 (html, json)

---

## 配置管理 API

### 获取提供商列表

**GET** `/config/providers`

### 添加提供商

**POST** `/config/providers`

**请求体**:
```json
{
    "name": "openai",
    "display_name": "OpenAI",
    "api_type": "openai",
    "api_key": "sk-xxx",
    "base_url": "https://api.openai.com",
    "models": ["gpt-4", "gpt-3.5-turbo"],
    "default_model": "gpt-3.5-turbo",
    "is_active": true
}
```

### 更新提供商

**PUT** `/config/providers/<name>`

### 删除提供商

**DELETE** `/config/providers/<name>`

### 测试提供商连接

**POST** `/config/providers/<name>/test`

### 获取提供商模型列表

**GET** `/config/providers/<name>/models`

---

## 字典管理 API

### 获取字典列表

**GET** `/dictionaries`

**查询参数**:
- `type`: 字典类型 (username, password)

### 上传字典

**POST** `/dictionaries`

支持文件上传或 JSON 请求。

**文件上传**:
```
Content-Type: multipart/form-data
- file: 字典文件
- name: 字典名称
- type: 字典类型
```

**JSON 请求**:
```json
{
    "name": "常用密码",
    "type": "password",
    "entries": ["123456", "password", "admin123"]
}
```

### 获取字典详情

**GET** `/dictionaries/<dict_id>`

### 删除字典

**DELETE** `/dictionaries/<dict_id>`

### 获取字典内容

**GET** `/dictionaries/<dict_id>/content`

### 预览字典

**GET** `/dictionaries/<dict_id>/preview?limit=50`

---

## WebSocket 事件

### 连接

```
ws://localhost:5000/socket.io
```

### 客户端事件

| 事件 | 参数 | 说明 |
|------|------|------|
| subscribe | `{task_id: "xxx"}` | 订阅任务更新 |
| unsubscribe | `{task_id: "xxx"}` | 取消订阅 |

### 服务端事件

| 事件 | 数据 | 说明 |
|------|------|------|
| connected | `{message: "..."}` | 连接成功 |
| task_progress | `{current, total, percent}` | 任务进度 |
| credential_found | `{username, password}` | 发现弱口令 |
| task_completed | `{summary}` | 任务完成 |
| log | `{level, message}` | 日志输出 |

---

## 示例用法

### 完整流程示例

```bash
# 1. 创建任务
curl -X POST http://localhost:5000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/login", "name": "测试"}'

# 2. 启动任务
curl -X POST http://localhost:5000/api/v1/tasks/task_xxx/start

# 3. 查看进度 (WebSocket)
# 使用 socket.io 客户端订阅任务更新

# 4. 获取报告
curl http://localhost:5000/api/v1/reports/task_xxx

# 5. 导出报告
curl http://localhost:5000/api/v1/reports/task_xxx/export?format=html -o report.html
```