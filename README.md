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
- **Deduplication** — always `filter_tasks(status:[0])` before creating (the `search` tool is unreliable on this server); skips creation when a title match already exists
- **No fabricated dates** — if the user didn't mention a date, it stays empty
- **Smart priority** — auto-assigns `0/1/3/5` by deadline proximity (today/tomorrow → High, 3–7 days → Medium, >7 days → Low)

**Routing & ops**
- **Dynamic project routing** — no hardcoded project IDs; discovers projects on first use and stores them in a local `config.json`
- **Full lifecycle** — create, query, update, complete, and delete through a consistent tool surface

**Visualization**
- **Kanban dashboard** — say "生成看板" / "task dashboard" (or `/task-dashboard` on Claude Code) to render all undone tasks bucketed by deadline urgency; switch the columns between due-date / priority / project. Three built-in skins (colorful / claude / notion).
- **Weekly report** — say "生成周报" (or `/week-report`) for a one-page A4 recap — this week's completed, overdue backlog, and next week's due — pulled live from TickTick into an HTML template and opened in your browser. Read-only snapshot; to change a task, say so in chat, the skill calls MCP, then you regenerate.

## How It Works

```
"提醒我明天下午3点开会"
  → Parse:    title="开会", due_date=2026-06-25T15:00:00+0800, priority=5
  → Route:    resolve project from config.json (Inbox by default)
  → Dedup:    filter_tasks(status:[0]) → no title match
  → Create:   create_task(task={"title":"开会", ...})
  → Confirm:  "已添加到滴答清单：开会 | 截止: 明天 15:00 | 优先级: 高"
```

## Prerequisites

- A **TickTick MCP server** connected to your AI agent, exposing the dida365 tools (`list_projects`, `create_task`, `search`, etc.). See [Connect the MCP server](#connect-the-ticktick-mcp-server) below — it's a one-time remote registration, no local package to install.

## Connect the TickTick MCP server

The TickTick MCP server is a **remote Streamable HTTP service** at `https://mcp.dida365.com` (server name `dida365`). Register it once with your agent runtime; auth is **OAuth** (browser, recommended) or a **Bearer Token**.

> **OAuth login helper.** Each platform ships `scripts/oauth_login.py` — a pure-Python (stdlib only) script that opens your browser to the TickTick login page and prints a Bearer token after you log in. Use it on runtimes that don't auto-open the browser (especially Claude Code, whose OAuth requires a manual `/mcp` step otherwise). Run `python scripts/oauth_login.py login`, then wire the printed `Authorization: Bearer …` line into your platform's MCP config below. **Token expiry:** dida365 does NOT support refresh tokens — its authorization-server metadata advertises only the `authorization_code` grant and rejects `offline_access`, so there is no `refresh` subcommand. When the token expires (401 / "Needs authentication"), just re-run `oauth_login.py login` to open the browser and log in again.

> If `dida365` is already registered, skip the `add` command in your platform's step and go straight to OAuth.

<details>
<summary><b>Claude Code</b></summary>

Claude Code's `claude mcp add` only writes config — OAuth normally needs a manual `/mcp` step. To skip it, run the login helper first, then register with the printed token:

```bash
python scripts/oauth_login.py login          # opens browser; prints "Authorization: Bearer <TOKEN>"
claude mcp add --transport http dida365 https://mcp.dida365.com --header "Authorization: Bearer <TOKEN>"
```

Or the manual `/mcp` path:

```bash
claude mcp add --transport http dida365 https://mcp.dida365.com
```
Then run `/mcp` in your session and complete OAuth in the browser.

</details>

<details>
<summary><b>OpenAI Codex</b></summary>

```bash
codex mcp add dida365 --url https://mcp.dida365.com
```
OAuth login is prompted automatically. If it is not, use the login helper and pass the token via an env var:

```bash
python scripts/oauth_login.py login
export DIDA365_TOKEN="<TOKEN>"
codex mcp remove dida365
codex mcp add dida365 --url https://mcp.dida365.com --bearer-token-env-var DIDA365_TOKEN
```

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
| `生成看板` | Renders the kanban dashboard in your browser (3 skins) |
| `生成周报` | Renders a one-page weekly report in your browser |

## Configuration

The skill stores project mapping in a local `config.json`. On first use it calls `list_projects()`, lists your projects, and asks you to pick a default.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `default_project` | string | `"Inbox"` | Default project for agent-created tasks |
| `projects` | object | `{}` | Name → ID mapping (auto-populated on first use) |
| `timezone` | string | `"Asia/Shanghai"` | Timezone for date calculations |

A ready-to-edit template ships at each platform's `config.example.json`.

## Directory Structure

```
ticktick-task-publish/
├── README.md  /  README_CN.md
├── src/                                    # Single source of truth (edit here)
│   ├── intro.md  body.md  visualization.md
│   ├── references/                         # ticktick-mcp-tools-reference.md + visualization-reference.md
│   ├── scripts/{oauth_login.py, config.example.json, templates/*.html}
│   ├── commands/{task-dashboard.md, week-report.md}      # Claude Code slash commands
│   └── platforms/<plat>/                  # frontmatter.md, mcp-setup.md, tail.md, <plat>.yml
├── scripts/
│   ├── build.py                            # Generator: src/ → 4 platform folders
│   └── bootstrap_src.py                    # One-shot: derive src/ from a canonical install
├── claude-code/                            # Claude Code (generated)
│   ├── .claude/skills/ticktick-task.md
│   ├── .claude/commands/{task-dashboard,week-report}.md
│   ├── scripts/{oauth_login.py, config.example.json, templates/*.html}
│   └── references/{ticktick-mcp-tools-reference, visualization-reference}.md
├── codex/                                  # OpenAI Codex (generated)
│   ├── codex.md
│   ├── scripts/{oauth_login.py, config.example.json, templates/*.html}
│   └── references/                         # same two reference files
├── hermes/                                 # Hermes Agent (generated)
│   └── ticktick-task/{SKILL.md, scripts/..., references/...}
└── openclaw/                               # OpenClaw / CLAWHUB (generated)
    └── .agents/skills/ticktick-task/{SKILL.md, scripts/..., references/...}
```

Each platform folder is **self-contained** — copy the whole folder into your setup. The four
folders are generated; see [Maintenance](#maintenance) below.

## Maintenance

The four platform folders (`claude-code/`, `codex/`, `hermes/`, `openclaw/`) are **generated**
from the single source under `src/` by `scripts/build.py`. Never hand-edit the generated folders —
edit `src/` and regenerate.

```bash
python scripts/build.py          # regenerate all 4 platform folders (idempotent)
python scripts/build.py --check  # exit 0 iff the working tree matches the generator output
```

Workflow:

1. Edit shared content in `src/` (`body.md`, `visualization.md`, `references/`, `scripts/templates/`,
   …) or a platform fragment in `src/platforms/<plat>/` (`frontmatter.md`, `mcp-setup.md`, `tail.md`).
2. Run `python scripts/build.py`.
3. Review the diff, then commit **both** `src/` and the regenerated folders.
4. Run `python scripts/build.py --check` to confirm the tree is in sync.

The build is deterministic: LF line endings, one trailing newline per file, no timestamps — running
it twice produces zero diff.

## Contributing

1. Fork this repo
2. Create your feature branch
3. Submit a pull request

## License

[MIT](LICENSE)
