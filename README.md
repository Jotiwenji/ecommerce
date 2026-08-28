# 旅游智能客服系统 · 掌柜小二（旅游版）

> 基于「三轨道对话引擎 + Flow 流程管理」构建的旅游行业智能客服，对接旅游数据中台 API，
> 覆盖商品咨询（酒店 / 景点 / 交通）、订单查询、退款售后、行程查询、工单提交等核心场景，
> 支持全链路 SSE 流式响应与业务对象消息（卡片）自动填槽。

## 1. 项目简介

本项目将一套通用电商客服对话引擎改造为**旅游行业**版本：重写 Flow 配置与 Action 层，
统一封装中台 `TravelAPIClient`，替换为 7 类旅游 FAQ 知识库，并把对话引擎的三条轨道
（Task / Knowledge / ChitChat）全链路接入 SSE 流式输出，前端提供一个开箱即用的对话式客服界面。

- **任务轨道**：10 个 YAML 定义的业务流程，驱动中台真实数据查询与业务办理
- **知识轨道**：7 类旅游 FAQ，LLM 基于 FAQ 内容生成自然回答
- **闲聊轨道**：统一"旅游小助手"人设兜底
- **意图路由**：`TurnPlanner` 调用 LLM 生成结构化 `TurnPlan`，`TurnPlanValidator` 校验，不通过则澄清

## 2. 系统架构

```
用户 ──HTTP── 前端(/ui) ──┬─▶ 客服后端 FastAPI
                          │     ├─ chat_router: /api/chat(非流式) /api/chat/stream(SSE) /api/chat/history /api/orders(代理) /api/chat/reset
                          │     ├─ DialogueService: 读写对话状态 + 调引擎
                          │     └─ DialogueEngine（三轨道）
                          │            ├─ TurnPlanner(LLM 路由) → Validator → ClarifyResponder
                          │            ├─ TaskHandler → FlowExecutor(两层循环) → ActionRunner → Actions
                          │            ├─ KnowledgeHandler → TravelFAQProvider + KnowledgeResponder(LLM)
                          │            └─ ChitChatHandler → ChitChatResponder(LLM)
                          │                     │
                          │     Actions ─ TravelAPIClient ─X-User-Id─▶ 旅游数据中台 API(:8000)
                          │     工单 Action ─▶ 独立工单库(work_orders)
                          └─ SSE: stage / progress / delta(逐token,已过滤推理模型think) / message / error / done
```

- **流程推进器**：内层循环推进步骤、外层循环执行 Action；Action 执行并写回槽位后再推进其条件分支。
- **流式**：LLM 调用统一走 `astream`，逐 token 推送；推理模型 `think` 内容在 `llm_streaming.py` 过滤，不污染 JSON 解析、不外泄给用户。
- **卡片自动填槽**：`OBJECT_TYPE_TO_SLOT` 将对象消息映射到对应流程槽位（order→orderId、hotel→hotelId、scenic_spot→scenicSpotId、flight/train/bus→departureId）。
- **序号下钻**：会话级 `last_search_results` 缓存上一轮搜索的有序 ID 与参数，"第 N 家 / 第 N 个"可解析为真实 ID 并恢复日期。

## 3. 核心能力

| 轨道 | 能力 |
|------|------|
| 任务 | 酒店查询/详情房型、景点查询/详情票种、交通查询(机票/火车/汽车)及班次详情、订单列表/详情、行程查询、退款申请(带状态校验/重复拦截)、工单提交(独立库)、商品推荐、转人工、欢迎引导 |
| 知识 | 酒店预订政策、景点门票政策、机票退改、火车票退改、支付发票、出行人证件、通用旅游 FAQ |
| 闲聊 | 旅游人设兜底 + 业务引导 |
| 交互 | 文本消息、卡片对象消息、SSE 全链路流式、会话持久化与恢复、意图澄清 |

## 4. 技术栈

- **语言/框架**：Python 3.13、FastAPI、Uvicorn
- **LLM 编排**：LangChain (`init_chat_model` + Jinja2 提示词模板)，OpenAI 兼容接口
- **数据访问**：SQLAlchemy 2.x (async) + aiomysql，双库（客服状态库 `customer_service` + 工单库 `work_orders`）
- **中台对接**：httpx 异步客户端，`X-User-Id` 头透传鉴权
- **前端**：原生 HTML / CSS / JS 单页，`StaticFiles` 挂载在 `/ui`，`fetch + ReadableStream` 解析 SSE

## 5. 项目结构

```
atguigu/
  api/            FastAPI 路由、依赖注入、请求/响应模型、app 入口(挂载 /ui)
  engine/         DialogueEngine(三轨道) + builder(装配)
  plan/           TurnPlanner(LLM 路由) + turn_plan 模型 + validator
  task/           流程：flows(loader/executor/links/steps) + action(register/builtin/customer) + command
  knowledge/      知识轨道：intents + providers(TravelFAQProvider) + faq_content + responder + handler
  chitchat/       闲聊轨道
  clarify/        意图澄清
  domain/         领域模型：messages / state(DialogueState) / contexts / object_slots
  history/        对话历史构建
  infrastructure/ llm / database / client(http) / work_order_database / streaming / llm_streaming
  prompt/jinja2/  提示词模板(turn_plan / knowledge_respond / chitchat_respond / clarify_respond)
  repository/     对话状态仓储 + 工单仓储/记录
  services/       DialogueService
flow_config/      system_flows.yml + user_flows.yml（10 业务流程）
docs/             PRD-旅游智能客服.md
frontend/         index.html + app.js + styles.css
```

## 6. 快速开始

### 依赖
- MySQL 8（本地 `127.0.0.1:3306`）
- 旅游数据中台服务，运行在 `http://127.0.0.1:8000`（另见中台项目）

### 安装
```bash
# 建议使用 uv
uv sync
# 或
pip install -e .
```

### 配置
复制 `.env.example` 为 `.env` 并填写：
```
LLM_MODEL=...                     # 模型名，支持推理模型(自动过滤 think)
LLM_BASE_URL=https://.../v1       # OpenAI 兼容 base_url
LLM_API_KEY=sk-...
TRAVEL_API_BASE_URL=http://127.0.0.1:8000/api/v1
TRAVEL_API_USER_HEADER=X-User-Id
TRAVEL_API_DEFAULT_USER_ID=13     # 须为中台 active 数字用户ID
DATABASE_URL=mysql+aiomysql://root:pwd@127.0.0.1:3306/customer_service?charset=utf8mb4
WORK_ORDER_DATABASE_URL=mysql+aiomysql://root:pwd@127.0.0.1:3306/work_orders?charset=utf8mb4
APP_HOST=0.0.0.0
APP_PORT=18082
```
数据库需先建库 `customer_service`（表 `dialogue_states`）与 `work_orders`（工单表启动时自动建）。

### 启动
```bash
uvicorn atguigu.api.app:app --host 127.0.0.1 --port 18082
```
- 前端：http://127.0.0.1:18082/ui/
- 接口文档：http://127.0.0.1:18082/docs

## 7. API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/chat` | 非流式对话，一次性返回完整回复 |
| POST | `/api/chat/stream` | SSE 流式对话：`stage/progress/delta/message/error/done` |
| GET | `/api/chat/history?sender_id=` | 获取会话历史（含卡片） |
| POST | `/api/chat/reset?sender_id=` | 清空卡住的活跃流程（保留历史） |
| GET | `/api/orders?sender_id=` | 代理中台订单列表，供前端"我的订单"侧栏发送卡片 |

对话请求体：
```json
{ "sender_id": "13", "text": "帮我查北京8月30日入住9月1日离店的酒店" }
{ "sender_id": "13", "object": { "id": "13", "type": "order", "title": "ORD0000000013", "attributes": {} } }
```

## 8. 测试与验收

对照 PRD 21 条验收标准（AC-01 ~ AC-21）逐条通过：酒店/景点/交通查询与序号下钻、
订单列表与详情、退款成功/状态拒绝/重复拦截、行程查询、工单提交、FAQ、转人工、闲聊、
意图路由、日期校验、SSE 流式（逐 token）、会话恢复、卡片消息、意图澄清。

## 9. 说明

- 本项目改造自通用电商客服对话引擎（课程实战项目），Flow 与 Action 层全部替换为旅游场景。
- `.env`、`.venv/`、`__pycache__/`、`.idea/` 已在 `.gitignore` 中排除，仓库不含依赖与密钥。
