# AI Model Gateway

统一的 AI 模型调用网关，支持 MiniMax / OpenAI / Anthropic 多模型接入。

## 功能特性

- **多模型支持**：MiniMax、OpenAI、Anthropic Claude
- **流式响应**：SSE 流式输出，实时交互体验
- **会话管理**：多轮对话持久化，支持会话历史
- **多租户**：JWT 认证，数据完全隔离
- **插件系统**：重试、熔断、限流插件
- **商业级架构**：Clean Architecture、依赖注入、单元测试

## 快速开始

### 1. 安装依赖

```bash
poetry install
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入你的 API Key
```

### 3. 初始化数据库

```bash
poetry run python scripts/init_db.py
```

### 4. 启动服务

```bash
poetry run uvicorn main:app --reload
```

### 5. 访问文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Docker 部署

```bash
docker-compose up -d
```

## 项目结构

```
aiModelStudy01/
├── adapters/          # 适配器层（LLM 模型对接）
├── application/       # 应用层（用例编排）
├── core/             # 核心业务（DTO/异常/接口）
├── infrastructure/    # 基础设施（DB/缓存/配置）
├── interfaces/        # 接口层（API/CLI）
├── plugins/          # 插件（重试/熔断/限流）
└── scripts/          # 运维脚本
```

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/auth/token | 获取访问令牌 |
| POST | /api/v1/chat | 单轮对话 |
| POST | /api/v1/chat/stream | 流式对话 |
| POST | /api/v1/session | 创建会话 |
| GET | /api/v1/session/{id} | 获取会话 |
| GET | /api/v1/session/{id}/messages | 获取历史消息 |
| GET | /health | 健康检查 |

## 开发

### 运行测试

```bash
poetry run pytest -v
```

### 代码检查

```bash
poetry run ruff check .
poetry run mypy .
```

## 许可证

MIT
