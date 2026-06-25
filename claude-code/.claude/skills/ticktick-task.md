<!-- TickTick Task Management Skill for Claude Code -->

# TickTick Task Management

Fast, smart task creation and management for TickTick (滴答清单) via MCP tools.

## When to Use

- User asks to create/add/write tasks to TickTick (滴答清单)
- User forwards notification text that should become a task
- User asks "what are my todos" or "what's due today"
- User says "remind me to..." or "帮我记一下..."
- User wants to update, complete, or delete TickTick tasks

## MCP Setup

This skill drives the **TickTick (滴答清单) MCP server**, a remote service at `https://mcp.dida365.com`. Claude Code must have it registered before any `mcp_ticktick_*` tool works.

**Guardrail.** If the `mcp_ticktick_*` tools are absent, or a call fails with "tool not found" / "Needs authentication" / "MCP not connected", **stop and run the onboarding below** — never fabricate task data, never silently skip. (Detection is reactive — on a failed or missing tool call — not a check at task start.)

**Onboarding — do this automatically:**

1. Run the registration command directly (do not ask first — it only adds a local config entry to `.claude.json`). If `dida365` is already registered, skip this and go to step 2:
   ```bash
   claude mcp add --transport http dida365 https://mcp.dida365.com
   ```
2. After it succeeds, **stop and hand off to the user** for the one step that cannot be automated: tell the user to type `/mcp` in this session's input box, then complete the TickTick OAuth login in the browser that opens. (The agent cannot type `/mcp` or complete OAuth itself — `/mcp` is a Claude Code session command, not a shell command the agent can run.)
3. Once the user confirms the `dida365` server is connected, retry the original task operation.

**Bearer Token alternative** (skips OAuth entirely — fully automatable): if the user provides a Bearer token, register with the header instead and no `/mcp` step is needed. The token must come from the user — never invent one:
```bash
claude mcp add --transport http dida365 https://mcp.dida365.com --header "Authorization: Bearer YOUR_TOKEN_HERE"
```
Get the token in 滴答清单 web → 头像 → 设置 → 账户与安全 → API 口令.

Official guide: https://help.dida365.com/articles/7438132116019216384

## First-Time Setup

On first invocation, if no project config exists:

1. Call `mcp_ticktick_get_projects()` to list all projects
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
  → Dedup: search_tasks(title) first
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

### Create

- **Single task**: `mcp_ticktick_create_task(title, project_id, content?, start_date?, due_date?, priority?)`
- **Batch (3+ tasks)**: `mcp_ticktick_batch_create_tasks(tasks=[{...}, ...])`
- **Subtask**: `mcp_ticktick_create_subtask(subtask_title, parent_task_id, project_id)`

### Query

| Tool | What it returns |
|------|----------------|
| `get_engaged_tasks()` | High priority + due today/overdue |
| `get_next_tasks()` | Medium priority + due tomorrow |
| `get_tasks_due_today()` | Tasks due today |
| `get_tasks_due_this_week()` | Tasks due within 7 days |
| `get_overdue_tasks()` | Overdue tasks |
| `search_tasks(search_term)` | Search by keyword |
| `get_project_tasks(project_id)` | All tasks in a project |

### Modify

- **Complete**: `mcp_ticktick_complete_task(project_id, task_id)`
- **Update**: `mcp_ticktick_update_task(task_id, project_id, title?, content?, due_date?, priority?)`
- **Delete**: `mcp_ticktick_delete_task(project_id, task_id)`

## Common Pitfalls

1. **Always dedup first** — Call `search_tasks` before creating. Duplicate tasks from repeated runs are the #1 issue.
2. **Date format must be ISO 8601 with timezone** — `2026-05-20T10:00:00+0800`, not `2026-05-20T10:00:00Z` unless user is in UTC.
3. **Don't fabricate dates** — If the user doesn't mention a date, leave it empty. Don't guess.
4. **project_id from config, never hardcode** — Always resolve through config.json or `get_projects()`. Project IDs differ per account.
5. **Preserve original links in content** — Users need to click through later.
6. **Batch for 3+ tasks** — Reduces API calls significantly.
7. **No due_date for undated tasks** — Don't set arbitrary deadlines on notes/memos.
8. **content two-part format** — Summary on top, separator `---`, original text below. This lets users scan quickly.

### Update Operations

When the user asks to update an existing task (e.g., change due date, title, or priority):
1. **Search first**: Call `search_tasks(title)` to locate the task (required for dedup and to get the task_id).
2. **Update**: Use `mcp_ticktick_update_task` with the found task_id and only the fields to be changed.
3. **Confirm**: Provide a one-line summary of the update.

Note: For update operations, set `dedup_searched: true` in the output block.

### Dedup Skip Behavior

When `search_tasks` finds a duplicate and the agent decides to skip creation:
- `action`: `dedup_skip`
- `title`: Set to the **intended task title** (the name the user gave or that would have been created).
- `priority`: Set to the priority that **would have been assigned** (e.g. `0` for an undated memo).
- `start_date`, `due_date`: Leave **blank** (no new task is being created).
- `content_summary`: Describe the skip reason, e.g. "Duplicate of existing task 'X', skipped".
- `dedup_searched`: Always `true`.

This ensures the output block reports what was intentionally skipped.

## Response Format

After creation, confirm concisely:

```
已添加到滴答清单 [项目名]：
- 任务标题 | 截止: 5/20 23:59 | 优先级: 高
```
