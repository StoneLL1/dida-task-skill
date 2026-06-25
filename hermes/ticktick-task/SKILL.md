---
name: ticktick-task
description: "Use when creating, managing, or querying TickTick tasks. Supports natural language date parsing, notification text extraction, batch creation, and smart project routing via dynamic config. Works with TickTick MCP tools."
version: 2.0.0
author: Hermes Agent Community
license: MIT
metadata:
  hermes:
    tags: [ticktick, task-management, reminders, notifications, productivity]
    related_skills: [wx-notification-skill]
prerequisites:
  commands: []
  env_vars: []
  mcp_servers: [ticktick]
---

# TickTick Task Management

Fast, smart task creation and management for TickTick (滴答清单) via MCP tools.

## When to Use

- User asks to create/add/write tasks to TickTick (滴答清单)
- User forwards notification text that should become a task
- User asks "what are my todos" or "what's due today"
- User says "remind me to..." or "帮我记一下..."
- User wants to update, complete, or delete TickTick tasks

## MCP Setup

This skill drives the **TickTick (滴答清单) MCP server**, a remote Streamable HTTP service at `https://mcp.dida365.com` (server name `dida365`). It must be registered with Hermes before any of its tools (`list_projects`, `create_task`, `search`, etc. — see `references/ticktick-mcp-tools-reference.md`) work.

**Guardrail.** If the dida365 tools are absent, or a call fails with "tool not found" / "Needs authentication" / "MCP not connected", **stop and run the onboarding below** — never fabricate task data, never silently skip. (Detection is reactive — on a failed or missing tool call — not a check at task start.)

**Onboarding — guide the user through this immediately when tools are missing (Hermes has no `add` CLI, so registration is done in Hermes's MCP config):**

1. Run the OAuth login helper shipped with this skill. It opens the user's browser to the TickTick login page and, after the user logs in and authorizes, prints a Bearer token (and saves it to `scripts/token.json`):
   ```bash
   python scripts/oauth_login.py login
   ```
2. Tell the user to register `https://mcp.dida365.com` as a Streamable HTTP MCP server named `dida365` in Hermes's MCP config, using the printed token as a Bearer header. If `dida365` is already registered, update its headers instead. Give them the exact values to paste: server name `dida365`, URL `https://mcp.dida365.com`, transport Streamable HTTP, header `Authorization: Bearer <PRINTED_TOKEN>`. (This skill's frontmatter declares the `ticktick` dependency, which the `dida365` endpoint satisfies.)
3. Once the user confirms the server is connected, retry the original task operation.

**Token expiry.** If a later call fails with 401 / "Needs authentication", the access token expired. Renew it: `python scripts/oauth_login.py refresh`, then tell the user to update the Bearer header in Hermes's config with the new printed token. If refresh exits non-zero, re-run `oauth_login.py login` to open the browser again.

**Bearer Token alternative** (long-lived, no browser): instead of the OAuth script, the user can create an API 口令 in 滴答清单 web → 头像 → 设置 → 账户与安全 → API 口令 and use it directly as the Bearer header value in step 2. The token must come from the user — never invent one.

Official guide: https://help.dida365.com/articles/7438132116019216384

## First-Time Setup

On first invocation, if no project config exists:

1. Call `list_projects()` to list all projects
2. Ask the user which project to use as default for agent-created tasks
3. Save to `config.json` in skill directory:
   ```json
   {
     "default_project": "Inbox",
     "projects": { "Inbox": "<id>" },
     "timezone": "Asia/Shanghai"
   }
   ```
4. On subsequent runs, load config.json; if a project name is not found, re-fetch project list

## Decision Rules

### Task Creation Flow

```
User input
  → Parse: title (required), content, dates, priority
  → Resolve project (user-specified → notification source → default)
  → Dedup: search(title) first
  → Create: single task OR batch (3+ items)
  → Confirm: one-line summary

- **Confirmation content**: Briefly state the action taken (e.g., 'Created task: ...', 'Skipped duplicate: ...') and whether dedup was searched. This provides immediate feedback and aligns with the output block.
```

### Project Routing

### Title Extraction Rules

For user-initiated tasks (not notification templates):
- Start with the entire user message as the title.
- Remove only explicit meta-phrases like "加个任务：", "帮我记一下", "提醒我" (and similar patterns).
- Keep all other words, including dates, locations, conditions, and auxiliary words like "要". For example, user says "7月15号之前办好签证" → title `7月15号之前办好签证`.
- The date, if present, will also be parsed into the date fields, but it must remain in the title for context.
- Do not add dates, locations, or priority indicators that the user did not mention — those belong in other fields.

| Source | Project | Rule |
|--------|---------|------|
| User specifies project | User's choice | Exact match on project name from config |
| Notification from WeChat group | Notification project | Look for "来源：xxx群" or group context |
| Agent-parsed from user message | Default project | Config `default_project` value |
| Fallback | Default project | Always have a default |

### Priority Assignment

| Value | Level | When to use |
|-------|-------|-------------|
| 0 | None | Normal memos, no deadline |
| 1 | Low | Non-urgent, distant deadline (>7 days) |
| 3 | Medium | Clear deadline, 3-7 days away |
| 5 | High | Today/tomorrow deadline, important meetings, urgent items |

**Auto-boost**: If notification text contains a deadline less than 3 days away (i.e. due today or tomorrow), default to High. A deadline exactly 3 days away falls in the Medium (3-7 day) band.

**Day counting and boundaries**: To determine the number of days until the due date, subtract today's date from the due date (in days). Use the following:
- 0–2 days (due today, tomorrow, or the day after tomorrow) → High (5)
- 3–7 days → Medium (3)
- 8 or more days → Low (1)

### Date Parsing Rules

Chinese natural language dates must be correctly converted:

- `5/20` → May 20 of current year
- `明天` → Tomorrow
- `下周三` → Next Wednesday
- `5月20号23:59` → `YYYY-05-20T23:59:00+0800`
- `截止5/30` → due_date only
- No specific time → due_date set to `23:59`, no start_date
- All dates in ISO 8601 with timezone offset (default `+0800` / `Asia/Shanghai`)

- **Events with a specific start time** (e.g., meeting, call): Set `start_date` to the event start time. If no end time is provided, set `due_date` to the same time (or leave it blank? but setting to the same time is acceptable). Priority: High if within 3 days, Medium otherwise.

### Notification Text Parsing Template

When user forwards notification/announcement text:

1. Extract: event name, time, location, key requirements/links
2. **title**: `Event - Time` or `Event - Deadline`
3. **content**:
   ```
   One-line summary (what, when, where, action needed)

   ---

   Original notification text (preserve links and source)
   ```
4. If deadline exists → High priority; if specific event time → Medium or High

## Tool Usage Guide

> Tool names below are the server's real names (see `references/ticktick-mcp-tools-reference.md`). The server does NOT provide `get_engaged_tasks` / `search_tasks` / `mcp_ticktick_*` — those are fictional. Task creation uses a `task` object with `title` + `projectId` (+ optional `content`, `dueDate`, `startDate`, `priority`, `tags`).

### Create

- **Single task**: `create_task(task={"title": ..., "projectId": ..., "dueDate": ..., "priority": ...})`
- **Batch (3+ tasks)**: `batch_add_tasks(tasks=[{"title":..., "projectId":...}, ...])`
- **Subtask**: set `parentId` on the task object in `create_task` (no separate subtask tool)

### Query

| Tool | What it returns |
|------|----------------|
| `list_undone_tasks_by_time_query(query_command="today")` | Undone tasks for today |
| `list_undone_tasks_by_time_query(query_command="tomorrow")` | Undone tasks due tomorrow |
| `list_undone_tasks_by_time_query(query_command="next7day")` | Undone tasks due within 7 days |
| `list_undone_tasks_by_date(search={"startDate":..., "endDate":...})` | Undone tasks in a date range (max 14 days) |
| `filter_tasks(filter={"priority":[5], "status":[0]})` | Structured filter (priority/status/tag/project) |
| `search(query="...")` | Keyword search — **use this for dedup** |
| `get_project_with_undone_tasks(project_id)` | Undone tasks in a project |

### Modify

- **Complete**: `complete_task(project_id, task_id)`
- **Update**: `update_task(task_id, task={"projectId":..., "dueDate":...})` — send only changed fields
- **Delete**: `delete_task(project_id, task_id)`

## Common Pitfalls

1. **Always dedup first** — Call `search(query=title)` before creating. Duplicate tasks from repeated runs are the #1 issue.
2. **Date format must be ISO 8601 with timezone** — `2026-05-20T10:00:00+0800`, not `2026-05-20T10:00:00Z` unless user is in UTC.
3. **Don't fabricate dates** — If the user doesn't mention a date, leave it empty. Don't guess.
4. **project_id from config, never hardcode** — Always resolve through config.json or `get_projects()`. Project IDs differ per account.
5. **Preserve original links in content** — Users need to click through later.
6. **Batch for 3+ tasks** — Reduces API calls significantly.
7. **No due_date for undated tasks** — Don't set arbitrary deadlines on notes/memos.
8. **content two-part format** — Summary on top, separator `---`, original text below. This lets users scan quickly.

### Update Operations

When the user asks to update an existing task (e.g., change due date, title, or priority):
1. **Search first**: Call `search(query=title)` to locate the task (required for dedup and to get the task_id).
2. **Update**: Use `update_task(task_id, task={"projectId":..., <only changed fields>})` with the found task_id.
3. **Confirm**: Provide a one-line summary of the update.

Note: For update operations, set `dedup_searched: true` in the output block.

### Dedup Skip Behavior

When `search` finds a duplicate and the agent decides to skip creation:
- `action`: `dedup_skip`
- `title`: Set to the **intended task title** (the name the user gave or that would have been created).
- `priority`: Set to the priority that **would have been assigned** (e.g. `0` for an undated memo).
- `start_date`, `due_date`: Leave **blank** (no new task is being created).
- `content_summary`: Describe the skip reason, e.g. "Duplicate of existing task 'X', skipped".
- `dedup_searched`: Always `true`.

This ensures the output block reports what was intentionally skipped.

## Common Scenarios

| Scenario | Action |
|----------|--------|
| "帮我创建一个任务" | Parse info, create directly. Ask if title missing. |
| User forwards notification text | Apply notification parsing template |
| "提醒我明天下午3点开会" | title="开会", start_date=tomorrow 15:00 |
| "把这条加到滴答清单" + text | Apply notification parsing template |
| "我有什么待办" | `list_undone_tasks_by_time_query("today")` + `list_undone_tasks_by_time_query("tomorrow")` |

## Response Format

After creation, confirm concisely:

```
已添加到滴答清单 [项目名]：
- 任务标题 | 截止: 5/20 23:59 | 优先级: 高
```

Batch creation: list all tasks.

## Verification Checklist

After creating a task, verify:
- [ ] Title is concise and actionable (not raw notification text)
- [ ] Due date matches user intent (not fabricated)
- [ ] Priority aligns with urgency rules above
- [ ] Project matches routing logic
- [ ] No duplicate exists (search returned empty)
- [ ] Response format is the one-line confirmation
