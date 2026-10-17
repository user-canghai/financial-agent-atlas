# Financial-Agent-AtlasServer

基于 LangChain、DeepAgents、MCP 与 Skills 的金融领域 Agent 示例项目。

## 功能

- MCP 服务器：网页抓取、黄金模拟交易、证券持仓、世界银行数据
- MCP 三元组件：Tools、Resources、Prompts
- 原生工具：联网搜索、Mock 财务数据、公司档案、天气、MCP 资源读取、AI 生图
- Skills：图文行业研究、公司分析、Python 业务技能
- SubAgent：`writer-agent`、`image-generator-agent`
- 运行方式：单轮对话、多轮 REPL、工具调用人工审核
- 文件工作区：报告、Markdown、配图

> 所有交易、行情和财务数据均为模拟数据，不连接真实交易所，不构成投资建议。

## 架构

```text
CLI / REPL
    │
    ▼
DeepAgent
    ├── Skills: /skills/*/SKILL.md
    ├── Native Tools: web_search, database_search, ...
    ├── MCP: fetch / gold_server / stock_server / worldbank
    ├── SubAgents: writer-agent / image-generator-agent
    └── Human-in-the-loop
    │
    ▼
/workspace/  /memories/  /skills/
```

## 环境要求

| 组件 | 版本 | 说明 |
| --- | --- | --- |
| Python | 3.11+ | 必需 |
| uv | 0.11+ | 推荐 |
| Node.js | 20+ | 可选，`worldbank` 需要 |

核心依赖见 `pyproject.toml`，其中 `deepagents==0.3.6` 固定版本。

## 快速开始

### 1. 安装依赖

```bash
cd Financial-Agent-AtlasServer
uv sync --extra dev
```

使用 pip：

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

最小配置：

```dotenv
QWEN_MODEL=qwen3-coder-plus
QWEN_API=你的模型APIKey
QWEN_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
BOCHA_API_KEY=你的博查APIKey
```

`QWEN_*` 是历史命名，实际支持任何 OpenAI 兼容接口。例如 DeepSeek：

```dotenv
QWEN_MODEL=deepseek-flash
QWEN_URL=https://api.deepseek.com/v1
QWEN_API=你的DeepSeekKey
```

注意：当前启动校验要求四个必需变量都存在，即使本次任务不使用联网搜索。`.env` 已被 `.gitignore` 忽略。

### 3. 环境自检

```bash
uv run main.py --check
uv run main.py --mcp-status
```

### 4. 运行

单轮：

```bash
uv run main.py --run "查询黄金账户状态和当前金价，不要交易，用中文汇报。"
```

多轮：

```bash
uv run main.py --interactive
uv run main.py -i
```

会话隔离：

```bash
uv run main.py -i --conversation gold-demo
```

调试节点：

```bash
uv run main.py --run "你的问题" --debug
```

## 配置项

| 变量 | 必需 | 说明 |
| --- | --- | --- |
| `QWEN_MODEL` | 是 | OpenAI 兼容模型名 |
| `QWEN_API` | 是 | 模型 API Key |
| `QWEN_URL` | 是 | OpenAI 兼容接口地址 |
| `BOCHA_API_KEY` | 是 | 博查搜索 API Key |
| `IMAGE_MODEL` | 否 | 图像模型，默认 `qwen-image-plus` |
| `IMAGE_SIZE_DEFAULT` | 否 | 默认 `1664*928` |
| `IMAGE_TIMEOUT` | 否 | 图像下载超时，默认 120 秒 |
| `TOOL_INTERRUPT_TIMEOUT` | 否 | 人工审核超时，默认 30 秒 |
| `AUTO_APPROVE_TOOLS` | 否 | `true` 时跳过人工审核 |
| `MCP_ENABLED_SERVERS` | 否 | 逗号分隔的 MCP 白名单 |
| `CUSTOM_SYSTEM_PROMPT` | 否 | 追加到系统提示词的自定义规则 |

图像生成使用 DashScope ImageSynthesis，并复用 `QWEN_API`。如果聊天模型使用 DeepSeek 等非 DashScope 服务，需要额外准备 DashScope Key 或扩展配置。

## MCP 服务器

| 服务器 | 启动方式 | 功能 |
| --- | --- | --- |
| `fetch` | `uvx mcp-server-fetch` | 网页抓取 |
| `gold_server` | 当前 Python 解释器 | 黄金模拟账户 |
| `stock_server` | 当前 Python 解释器 | 证券持仓模拟 |
| `worldbank` | `npx -y worldbank-mcp` | 世界银行数据 |

没有 Node.js 时：

```dotenv
MCP_ENABLED_SERVERS=fetch,gold_server,stock_server
```

### 黄金服务器

- Resource：`account://status`
- Tools：`buy_gold`、`sell_gold`、`deposit`、`withdraw`、`get_gold_price`
- Prompt：`instruction_manual`
- 数据文件：`gold_account.json`，首次运行自动创建，初始为 100,000 元现金 + 166.67 克黄金

示例：

```bash
uv run main.py --run "请按以下步骤操作黄金账户：
1. 查询账户状态
2. 获取当前金价
3. 模拟买入 10 克黄金
4. 验证交易结果"
```

### 证券服务器

- Resource：`portfolio://status`
- Tools：`get_stock_price`、`buy_stock`、`sell_stock`、`deposit_cash`、`withdraw_cash`
- Prompt：`instruction_manual`

MCP 工具在 Agent 中会带服务器前缀，例如 `gold_server_buy_gold`。只读 Resource 可以通过原生工具 `read_mcp_resource` 读取。

## Skills

### 工作流 Skill

- `skills/industry-research-with-image/SKILL.md`：规划框架 → 收集信息 → 生成图片 → 撰写内容 → 定稿
- `skills/analyze-company/SKILL.md`：公司概况、财务、业务模式、风险分析

### Python 业务技能

`skills/common`、`skills/finance`、`skills/research` 下的 `BaseSkill` 子类可以通过 `Financial_Agent.skills.loader` 程序化调用。

`src/Financial_Agent/mcp/skills.py` 提供 `SKILL.md` 的列表与读取能力，不负责执行 Python 技能。

## 项目结构

```text
Financial-Agent-AtlasServer/
├── main.py
├── pyproject.toml
├── .env.example
├── src/Financial_Agent/
│   ├── agent/
│   ├── core/
│   ├── mcp/
│   │   └── servers/
│   ├── memory/
│   ├── repl/
│   ├── skills/
│   ├── subagents/
│   ├── tools/
│   ├── config.py
│   └── diagnostics.py
├── skills/
│   ├── industry-research-with-image/
│   ├── analyze-company/
│   ├── common/
│   ├── finance/
│   ├── research/
│   └── base.py
└── workspaces/
```

## 虚拟文件系统

| 虚拟路径 | 实际目录 | 用途 |
| --- | --- | --- |
| `/workspace/` | `workspaces/` | 报告、Markdown、临时文件 |
| `/workspace/pic/` | `workspaces/pic/` | 报告配图 |
| `/skills/` | `skills/` | Skill 定义 |
| `/memories/` | `memories/` | 会话历史与长期记忆 |
| `/tools/` | `src/Financial_Agent/tools/` | 原生工具源码 |
| `/mcp_servers/` | `src/Financial_Agent/mcp/servers/` | MCP 服务器源码 |

## 人工审核

以下工具默认会触发人工审核：

- `web_search`
- `database_search`
- `edit_file`
- `mkdir`

默认等待 30 秒，超时自动批准；非交互环境也会自动批准。设置 `AUTO_APPROVE_TOOLS=true` 可跳过审核。

## 常见问题

### `worldbank` 启动失败

未安装 Node.js 或 `npx`。从 `MCP_ENABLED_SERVERS` 中移除 `worldbank`。

### `fetch` 首次启动较慢

`uvx` 首次运行会下载 `mcp-server-fetch`，后续会使用缓存。

### 图像生成失败

- 检查 `QWEN_API` 是否可用于 DashScope ImageSynthesis；
- 检查 `IMAGE_MODEL`；
- 检查 `IMAGE_SIZE_DEFAULT` 是否为支持的尺寸。

### 没有 API Key 能运行吗？

可以运行单元测试、`--check`、MCP 服务器和工具级测试；完整 Agent 对话需要模型和搜索凭证。

## 说明

本项目仅用于学习、研究与演示。所有交易、行情和财务数据均为模拟数据，不连接真实交易所，不构成投资建议。
