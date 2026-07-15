<div align="center">

# TickTick 任务管理 Skill

**跨平台 AI Agent Skill，通过 MCP 工具管理 TickTick（滴答清单）任务**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platforms](https://img.shields.io/badge/platforms-Hermes%20%7C%20OpenClaw%20%7C%20Claude%20Code%20%7C%20Codex-green.svg)](#安装)
[![MCP](https://img.shields.io/badge/协议-MCP-blueviolet.svg)](#前置要求)

[English](README.md) · 中文文档

</div>

---

滴答清单很擅长记录任务，而这个 Skill 赋予你的 AI Agent 用好它的「纪律」——把零散的自然语言输入，干净地解析成去重、日期正确、优先级合理的任务，并支持四大主流 Agent 运行时。

## 功能特性

**捕获**
- **自然语言建任务** — 中英文日期解析（`明天`、`下周三`、`5/20`、`5月20号23:59`），输出 ISO 8601 带时区格式
- **通知转任务** — 转发任意通知/公告文本，自动提取事件、时间、地点与链接，生成结构化任务（摘要 + 保留原文）
- **批量创建** — 3 个以上任务用 `batch_create_tasks` 一次搞定

**质量护栏**
- **自动去重** — 创建前一律 `filter_tasks(status:[0])` 拉全量未完成再按标题比对（本服务端 `search` 不可靠）；若已存在相同任务则跳过创建
- **不臆造日期** — 用户没提日期就留空，绝不乱猜
- **智能优先级** — 按截止日期远近自动分配 `0/1/3/5`（今天/明天=高，3–7 天=中，>7 天=低）

**路由与操作**
- **动态项目路由** — 不硬编码项目 ID；首次使用时自动发现项目并存入本地 `config.json`
- **完整生命周期** — 创建、查询、更新、完成、删除，统一的工具接口

**可视化**
- **任务看板** — 说"生成看板"/"任务看板"（或 Claude Code 用 `/task-dashboard`）渲染日程仪表盘：未完成任务按截止紧迫度分桶，可切换"截止日 / 优先级 / 项目"维度。内置三套皮肤（彩色 / claude / notion）。
- **周报** — 说"生成周报"（或 `/week-report`）生成一页 A4 周报：本周完成 / 过期阻塞 / 下周到期，从 TickTick 实时拉数据注入 HTML 模板并在浏览器打开。只读快照——要改任务回对话里说，skill 调 MCP 后重新生成即可。

## 工作原理

```
"提醒我明天下午3点开会"
  → 解析：   title="开会", due_date=2026-06-25T15:00:00+0800, priority=5
  → 路由：   从 config.json 解析项目（默认 Inbox）
  → 去重：   filter_tasks(status:[0]) → 无标题重复
  → 创建：   create_task(task={"title":"开会", ...})
  → 确认：   "已添加到滴答清单：开会 | 截止: 明天 15:00 | 优先级: 高"
```

## 前置要求

- 已为你的 AI Agent 连接 **TickTick MCP Server**，提供 dida365 工具（`list_projects`、`create_task`、`search` 等）。参见下文[连接 MCP Server](#连接-ticktick-mcp-server)——这是一次性的远程注册，无需本地安装包。

## 连接 TickTick MCP Server

TickTick MCP Server 是一个**远程 Streamable HTTP 服务**，地址 `https://mcp.dida365.com`（服务名 `dida365`）。在你的 Agent 运行时里注册一次即可；授权用 **OAuth**（浏览器，推荐）或 **Bearer Token**。

> **OAuth 登录脚本。** 每个平台附带 `scripts/oauth_login.py`（纯 Python 标准库，无第三方依赖），运行后会自动打开浏览器到滴答清单登录页，登录授权后打印一个 Bearer token。用于那些不会自动弹浏览器的运行时（尤其是 Claude Code——否则要手动敲 `/mcp`）。用法：`python scripts/oauth_login.py login`，然后把打印的 `Authorization: Bearer …` 配进你所在平台的 MCP 配置。**关于 token 过期：** dida365 **不支持** refresh token——其授权服务器元数据只声明 `authorization_code` 授权，且会拒绝 `offline_access`，因此没有 `refresh` 子命令。token 过期时（401 / "Needs authentication"），直接重跑 `oauth_login.py login`，重新打开浏览器登录即可。

> 若 `dida365` 已注册，跳过你所在平台步骤里的 `add` 命令，直接进入 OAuth。

<details>
<summary><b>Claude Code</b></summary>

Claude Code 的 `claude mcp add` 只写配置——OAuth 通常要手动敲 `/mcp`。要跳过这一步，先跑登录脚本拿到 token，再带 token 注册：

```bash
python scripts/oauth_login.py login          # 打开浏览器；打印 "Authorization: Bearer <TOKEN>"
claude mcp add --transport http dida365 https://mcp.dida365.com --header "Authorization: Bearer <TOKEN>"
```

或走手动 `/mcp` 路径：

```bash
claude mcp add --transport http dida365 https://mcp.dida365.com
```
然后在会话中运行 `/mcp`，在浏览器完成 OAuth 授权。

</details>

<details>
<summary><b>OpenAI Codex</b></summary>

```bash
codex mcp add dida365 --url https://mcp.dida365.com
```
命令执行后会自动提示完成 OAuth 登录。若未自动弹，用登录脚本拿 token 再通过环境变量传入：

```bash
python scripts/oauth_login.py login
export DIDA365_TOKEN="<TOKEN>"
codex mcp remove dida365
codex mcp add dida365 --url https://mcp.dida365.com --bearer-token-env-var DIDA365_TOKEN
```

</details>

<details>
<summary><b>Cursor / VS Code / TRAE / WorkBuddy</b>（JSON 配置）</summary>

Cursor — 编辑 `.cursor/mcp.json`：
```json
{
  "mcpServers": {
    "dida365": { "url": "https://mcp.dida365.com" }
  }
}
```
VS Code — 编辑 `.vscode/mcp.json`：
```json
{
  "servers": {
    "dida365": { "type": "http", "url": "https://mcp.dida365.com" }
  }
}
```
保存后连接 `dida365`，在浏览器完成 OAuth 授权。

</details>

<details>
<summary><b>Claude Desktop / ChatGPT</b>（界面连接器）</summary>

- **Claude Desktop**：Customize → Connectors → Add Connector → 填 URL `https://mcp.dida365.com` → Connect → OAuth。
- **ChatGPT**：设置 → 应用 → 高级设置 → 开启开发人员模式 → 创建应用 → 填 URL `https://mcp.dida365.com` → OAuth。

</details>

**鉴权说明**
- OAuth（浏览器）为默认推荐方式。
- Bearer Token 备选：在 滴答清单 web → 头像 → 设置 → 账户与安全 → API 口令 创建。
- 完整指南：https://help.dida365.com/articles/7438132116019216384

> 想用命令行而非 MCP？`dida-cli`（`npm i -g @suibiji/dida-cli`）是独立的命令行工具，用于管理滴答清单任务——是 MCP 之外的备选方案，本 Skill 不依赖它。详见 https://www.npmjs.com/package/@suibiji/dida-cli。

预期工具接口见 [`references/ticktick-mcp-tools-reference.md`](hermes/ticktick-task/references/ticktick-mcp-tools-reference.md)。

## 安装

每个平台文件夹都是**自包含**的——整个复制即可使用。选择你的运行时：

<details>
<summary><b>Hermes Agent</b></summary>

```bash
cp -r hermes/ticktick-task ~/.hermes/skills/productivity/
```

</details>

<details>
<summary><b>OpenClaw</b></summary>

```bash
# 方式 A：把整个 .agents 目录复制进项目
cp -r openclaw/.agents /path/to/project/

# 方式 B：只复制 skill
cp -r openclaw/.agents/skills/ticktick-task /path/to/project/.agents/skills/
```

</details>

<details>
<summary><b>Claude Code</b></summary>

```bash
# 全局（所有项目生效）
cp -r claude-code/.claude ~/.claude/

# 项目级
cp -r claude-code/.claude /path/to/your/project/.claude/
```

</details>

<details>
<summary><b>OpenAI Codex</b></summary>

```bash
# 追加到已有 AGENTS.md
cat codex/codex.md >> /path/to/your/project/AGENTS.md

# 或作为独立文件
cp codex/codex.md /path/to/your/project/codex.md
```

</details>

## 快速开始

安装完成后，试试这些指令：

| 你说 | 发生了什么 |
|------|-----------|
| `帮我创建一个任务：周五前提交报告` | 创建任务，截止到周五 |
| `提醒我明天下午3点开会` | 创建任务，截止明天 15:00，优先级高 |
| `把这段通知加到滴答清单` + 粘贴文本 | 通知被解析为结构化任务 |
| `我有什么待办？` | 显示高优先级与近期待办 |
| `完成 XXX 任务` | 搜索并完成匹配的任务 |
| `生成看板` | 在浏览器渲染任务看板（三套皮肤） |
| `生成周报` | 在浏览器生成本周一页周报 |

## 配置说明

Skill 把项目映射存在本地 `config.json`。首次使用时调用 `list_projects()` 列出项目，让你选择默认项目。

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `default_project` | string | `"Inbox"` | Agent 创建任务的默认项目 |
| `projects` | object | `{}` | 名称 → ID 映射（首次使用时自动填充） |
| `timezone` | string | `"Asia/Shanghai"` | 日期计算的时区 |

各平台都附带可直接编辑的 `config.example.json` 模板。

## 目录结构

```
ticktick-task-publish/
├── README.md  /  README_CN.md
├── src/                                    # 单一真相源（在这里改）
│   ├── intro.md  body.md  visualization.md
│   ├── references/                         # ticktick-mcp-tools-reference.md + visualization-reference.md
│   ├── scripts/{oauth_login.py, config.example.json, templates/*.html}
│   ├── commands/{task-dashboard.md, week-report.md}      # Claude Code 斜杠命令
│   └── platforms/<plat>/                   # frontmatter.md、mcp-setup.md、tail.md、<plat>.yml
├── scripts/
│   ├── build.py                            # 生成器：src/ → 4 个平台目录
│   └── bootstrap_src.py                    # 一次性脚本：从 canonical 安装推导出 src/
├── claude-code/                            # Claude Code（生成产物）
│   ├── .claude/skills/ticktick-task.md
│   ├── .claude/commands/{task-dashboard,week-report}.md
│   ├── scripts/{oauth_login.py, config.example.json, templates/*.html}
│   └── references/{ticktick-mcp-tools-reference, visualization-reference}.md
├── codex/                                  # OpenAI Codex（生成产物）
│   ├── codex.md
│   ├── scripts/{oauth_login.py, config.example.json, templates/*.html}
│   └── references/                         # 同样两份参考文档
├── hermes/                                 # Hermes Agent（生成产物）
│   └── ticktick-task/{SKILL.md, scripts/..., references/...}
└── openclaw/                               # OpenClaw / CLAWHUB（生成产物）
    └── .agents/skills/ticktick-task/{SKILL.md, scripts/..., references/...}
```

每个平台目录都**自包含**——把整个目录复制进你的配置即可。四个目录均为生成产物，见下方[维护](#维护)。

## 维护

四个平台目录（`claude-code/`、`codex/`、`hermes/`、`openclaw/`）都由 `scripts/build.py` 从
`src/` 单源**生成**。请勿手改生成目录——改 `src/` 后重新生成。

```bash
python scripts/build.py          # 重新生成 4 个平台目录（幂等）
python scripts/build.py --check  # 当且仅当工作区与生成器输出一致时退出码 0
```

流程：

1. 改 `src/` 里的共享内容（`body.md`、`visualization.md`、`references/`、`scripts/templates/` …），
   或 `src/platforms/<plat>/` 里的平台片段（`frontmatter.md`、`mcp-setup.md`、`tail.md`）。
2. 运行 `python scripts/build.py`。
3. review diff 后，**同时**提交 `src/` 与重新生成的目录。
4. 运行 `python scripts/build.py --check` 确认工作区与生成器一致。

构建是确定性的：统一 LF 行尾、每个文件单个末尾换行、无时间戳——连跑两次零 diff。

## 许可证

[MIT](LICENSE)
