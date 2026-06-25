<div align="center">

# TickTick Task Management Skill

**Cross-platform AI agent skill for managing TickTick (滴答清单) tasks via MCP tools**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platforms](https://img.shields.io/badge/platforms-Hermes%20%7C%20OpenClaw%20%7C%20Claude%20Code%20%7C%20Codex-green.svg)](#installation)
[![MCP](https://img.shields.io/badge/protocol-MCP-blueviolet.svg)](#prerequisites)

[English](#features) · [中文文档](README_CN.md)

</div>

---

TickTick is great for capturing tasks; this skill gives your AI agent the *discipline* to use it well — parsing messy natural-language input into clean, de-duplicated, correctly-dated, correctly-prioritized tasks across four major agent runtimes.

## Features

**Capture**
- **Natural-language task creation** — Chinese & English date parsing (`明天`, `下周三`, `5/20`, `5月20号23:59`) with ISO 8601 + timezone output
- **Notification-to-task** — forward any announcement/notification text; the skill extracts event, time, location, and links into a structured task (summary + preserved original)
- **Batch creation** — 3+ tasks in a single `batch_create_tasks` call

**Quality guardrails**
- **Deduplication** — always `search_tasks` before creating; skips creation when a match already exists
- **No fabricated dates** — if the user didn't mention a date, it stays empty
- **Smart priority** — auto-assigns `0/1/3/5` by deadline proximity (today/tomorrow → High, 3–7 days → Medium, >7 days → Low)

**Routing & ops**
- **Dynamic project routing** — no hardcoded project IDs; discovers projects on first use and stores them in a local `config.json`
- **Full lifecycle** — create, query, update, complete, and delete through a consistent tool surface

## How It Works

```
"提醒我明天下午3点开会"
  → Parse:    title="开会", due_date=2026-06-25T15:00:00+0800, priority=5
  → Route:    resolve project from config.json (Inbox by default)
  → Dedup:    search_tasks("开会") → no match
  → Create:   mcp_ticktick_create_task(...)
  → Confirm:  "已添加到滴答清单：开会 | 截止: 明天 15:00 | 优先级: 高"
```

## Prerequisites

- A **TickTick MCP server** connected to your AI agent, exposing the `mcp_ticktick_*` tools. See [Connect the MCP server](#connect-the-ticktick-mcp-server) below — it's a one-time remote registration, no local package to install.

## Connect the TickTick MCP server

The TickTick MCP server is a **remote Streamable HTTP service** at `https://mcp.dida365.com` (server name `dida365`). Register it once with your agent runtime; auth is **OAuth** (browser, recommended) or a **Bearer Token**.

> If `dida365` is already registered, skip the `add` command in your platform's step and go straight to OAuth.

<details>
<summary><b>Claude Code</b></summary>

```bash
claude mcp add --transport http dida365 https://mcp.dida365.com
```
Then run `/mcp` in your session and complete OAuth in the browser.

Bearer Token variant:
```bash
claude mcp add --transport http dida365 https://mcp.dida365.com --header "Authorization: Bearer YOUR_TOKEN_HERE"
```

</details>

<details>
<summary><b>OpenAI Codex</b></summary>

```bash
codex mcp add dida365 --url https://mcp.dida365.com
```
OAuth login is prompted automatically.

</details>

<details>
<summary><b>Cursor / VS Code / TRAE / WorkBuddy</b> (JSON config)</summary>

Cursor — edit `.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "dida365": { "url": "https://mcp.dida365.com" }
  }
}
```
VS Code — edit `.vscode/mcp.json`:
```json
{
  "servers": {
    "dida365": { "type": "http", "url": "https://mcp.dida365.com" }
  }
}
```
Save, then connect `dida365` and complete OAuth in the browser.

</details>

<details>
<summary><b>Claude Desktop / ChatGPT</b> (UI connectors)</summary>

- **Claude Desktop**: Customize → Connectors → Add Connector → URL `https://mcp.dida365.com` → Connect → OAuth.
- **ChatGPT**: Settings → Apps → Advanced → enable Developer mode → Create app → URL `https://mcp.dida365.com` → OAuth.

</details>

**Auth notes**
- OAuth (browser) is the default and recommended path.
- Bearer Token alternative: create one at 滴答清单 web → 头像 → 设置 → 账户与安全 → API 口令.
- Full guide: https://help.dida365.com/articles/7438132116019216384

> Prefer a CLI instead of MCP? `dida-cli` (`npm i -g @suibiji/dida-cli`) is an independent command-line tool for managing TickTick tasks — a non-MCP alternative, not required by this skill. See https://www.npmjs.com/package/@suibiji/dida-cli.

The expected tool surface is documented in [`references/ticktick-mcp-tools-reference.md`](hermes/ticktick-task/references/ticktick-mcp-tools-reference.md).

## Installation

Each platform folder is **self-contained** — copy the whole folder and you're ready. Pick your runtime:

<details>
<summary><b>Hermes Agent</b></summary>

```bash
cp -r hermes/ticktick-task ~/.hermes/skills/productivity/
```

</details>

<details>
<summary><b>OpenClaw</b></summary>

```bash
# Option A — copy the entire .agents tree into your project
cp -r openclaw/.agents /path/to/project/

# Option B — copy only the skill
cp -r openclaw/.agents/skills/ticktick-task /path/to/project/.agents/skills/
```

</details>

<details>
<summary><b>Claude Code</b></summary>

```bash
# Global (all projects)
cp -r claude-code/.claude ~/.claude/

# Project-level
cp -r claude-code/.claude /path/to/your/project/.claude/
```

</details>

<details>
<summary><b>OpenAI Codex</b></summary>

```bash
# Append to existing AGENTS.md
cat codex/codex.md >> /path/to/your/project/AGENTS.md

# ...or keep as a standalone file
cp codex/codex.md /path/to/your/project/codex.md
```

</details>

## Quick Start

After installation, try these with your agent:

| You say | What happens |
|---------|-------------|
| `帮我创建一个任务：周五前提交报告` | Task created, due Friday |
| `提醒我明天下午3点开会` | Task with due date tomorrow 15:00, priority High |
| `把这段通知加到滴答清单` + paste text | Notification parsed into a structured task |
| `我有什么待办？` | Shows engaged + upcoming tasks |
| `完成 XXX 任务` | Searches and completes the matching task |

## Configuration

The skill stores project mapping in a local `config.json`. On first use it calls `get_projects()`, lists your projects, and asks you to pick a default.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `default_project` | string | `"Inbox"` | Default project for agent-created tasks |
| `projects` | object | `{}` | Name → ID mapping (auto-populated on first use) |
| `timezone` | string | `"Asia/Shanghai"` | Timezone for date calculations |

A ready-to-edit template ships at each platform's `config.example.json`.

## Directory Structure

```
ticktick-task-publish/
├── README.md                                # This file
├── README_CN.md                             # 中文说明
├── hermes/                                  # Hermes Agent
│   └── ticktick-task/
│       ├── SKILL.md                         # Skill definition (YAML frontmatter + body)
│       ├── config.example.json
│       └── references/ticktick-mcp-tools-reference.md
├── openclaw/                                # OpenClaw / CLAWHUB
│   └── .agents/skills/ticktick-task/
│       ├── SKILL.md
│       ├── config.example.json
│       └── references/ticktick-mcp-tools-reference.md
├── claude-code/                             # Claude Code
│   ├── .claude/skills/ticktick-task.md      # Skill instructions
│   ├── scripts/config.example.json
│   └── references/ticktick-mcp-tools-reference.md
└── codex/                                   # OpenAI Codex
    ├── codex.md                             # AGENTS.md-style instructions
    ├── scripts/config.example.json
    └── references/ticktick-mcp-tools-reference.md
```

## Contributing

1. Fork this repo
2. Create your feature branch
3. Submit a pull request

## License

[MIT](LICENSE)
