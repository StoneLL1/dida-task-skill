---
name: ticktick-task
description: |
  滴答清单（TickTick）任务管理。当用户要求创建/添加/查询/完成/更新/删除滴答清单任务、
  转发通知文本转为任务、问"我有什么待办""今天到期什么"、或说"提醒我…""帮我记一下…"
  时使用。通过 dida365 MCP 工具自动去重、中英文日期解析、按截止日智能分配优先级。
  也支持可视化：说"生成看板/任务看板"或 `/task-dashboard` 生成日程仪表盘（三套皮肤），
  说"生成周报"或 `/week-report` 生成本周周报——均从 TickTick 拉数据注入 HTML 模板。
---

# TickTick Task Management

Fast, smart task creation and management for TickTick (滴答清单) via MCP tools.

## When to Use

- User asks to create/add/write tasks to TickTick (滴答清单)
- User forwards notification text that should become a task
- User asks "what are my todos" or "what's due today"
- User says "remind me to..." or "帮我记一下..."
- User wants to update, complete, or delete TickTick tasks
- User says "生成看板" / "任务看板" / `/task-dashboard` → render the dashboard (ask which skin)
- User says "生成周报" / `/week-report` → render the weekly report

## MCP Setup

This skill drives the **TickTick (滴答清单) MCP server**, a remote service at `https://mcp.dida365.com`. Claude Code must have it registered before any of its tools (`list_projects`, `create_task`, `search`, etc. — see `references/ticktick-mcp-tools-reference.md`) work. On Claude Code the tools appear as `mcp__dida365__<tool>`.

**Guardrail.** If the dida365 tools are absent, or a call fails with "tool not found" / "Needs authentication" / "MCP not connected", **stop and run the onboarding below** — never fabricate task data, never silently skip. (Detection is reactive — on a failed or missing tool call — not a check at task start.)

**Onboarding — do this automatically:**

1. Run the OAuth login helper shipped with this skill. It opens the user's browser to the TickTick login page and, after the user logs in and authorizes, prints a Bearer token (and saves it to `scripts/token.json`):
   ```bash
   python scripts/oauth_login.py login
   ```
   If the browser does not open automatically, the script prints the URL to visit manually. This bypasses the `/mcp` step entirely.
2. Register the MCP server with that token (use the exact `Authorization: Bearer …` line the script printed). If `dida365` is already registered, remove it first with `claude mcp remove dida365`:
   ```bash
   claude mcp add --transport http dida365 https://mcp.dida365.com --header "Authorization: Bearer <PRINTED_TOKEN>"
   ```
3. Retry the original task operation.

**Token expiry.** If a later call fails with 401 / "Needs authentication", the access token expired. dida365 does NOT support refresh tokens (its metadata advertises only the `authorization_code` grant and rejects `offline_access`), so there is no `refresh` subcommand. Re-run the login helper to get a fresh token, then re-register:
   ```bash
   python scripts/oauth_login.py login
   ```
   Then re-run step 2 with the new printed token.

**Bearer Token alternative** (long-lived, no browser): instead of the OAuth script, the user can create an API 口令 in 滴答清单 web → 头像 → 设置 → 账户与安全 → API 口令 and pass it directly to the `--header` in step 2. The token must come from the user — never invent one.

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
  → Dedup: filter_tasks(status:[0]) + 标题比对（search 不可靠，见 Tool Usage Guide）
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
>
> **⚠ 去重别用 `search`**：`search` / `search_task` 在 dida365 MCP 服务端经常返回 `[]`（即使任务确实存在；2026-07 实测对「技能自测」「党员」「六级考试」及完整标题均返回空）。**去重、按标题定位一律用 `filter_tasks(filter={"status":[0]})` 拉全量未完成，再在客户端按标题比对**（归一化：去首尾空格 + 合并连续空格 + 忽略大小写）。

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
| `search` / `search_task` | ⚠ **不可靠**：本服务端常返回空，**不要用于去重**。按标题查找改用 `filter_tasks` + 客户端比对 |
| `get_project_with_undone_tasks(project_id)` | Undone tasks in a project |

### Modify

- **Complete**: `complete_task(project_id, task_id)`
- **Update**: `update_task(task_id, task={"projectId":..., "dueDate":...})` — send only changed fields
- **Delete**: `delete_task(project_id, task_id)`

## Common Pitfalls

1. **Always dedup first — 用 `filter_tasks`，不要用 `search`** — 创建前先 `filter_tasks(filter={"status":[0]})` 拉全部未完成，在客户端按标题比对（去空格、忽略大小写）。`search`/`search_task` 在本服务端常返回空，不可靠。重复创建是头号问题。
2. **Date format must be ISO 8601 with timezone** — `2026-05-20T10:00:00+0800`, not `2026-05-20T10:00:00Z` unless user is in UTC.
3. **Don't fabricate dates** — If the user doesn't mention a date, leave it empty. Don't guess.
4. **project_id from config, never hardcode** — Always resolve through config.json or `get_projects()`. Project IDs differ per account.
5. **Preserve original links in content** — Users need to click through later.
6. **Batch for 3+ tasks** — Reduces API calls significantly.
7. **No due_date for undated tasks** — Don't set arbitrary deadlines on notes/memos.
8. **content two-part format** — Summary on top, separator `---`, original text below. This lets users scan quickly.

### Update Operations

When the user asks to update an existing task (e.g., change due date, title, or priority):
1. **Find the task via `filter_tasks`**（不要用 `search`，见 Common Pitfalls #1）：`filter_tasks(filter={"status":[0]})`（或按 project/tag 收窄）拉任务，按标题比对拿到 `task_id` 与 `projectId`。
2. **Update**: Use `update_task(task_id, task={"projectId":..., <only changed fields>})` with the found task_id.
3. **Confirm**: Provide a one-line summary of the update.

Note: For update operations, set `dedup_searched: true` in the output block.

### Dedup Skip Behavior

When dedup（`filter_tasks` + 标题比对）finds a duplicate and the agent decides to skip creation:
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

## Visualization（看板 / 周报）

把 TickTick 数据渲染成自包含 HTML，浏览器打开。**只读快照**——页面里的拖拽/勾选/新建都是本地预览，不同步回滴答；要真正改任务回对话说，再「刷新看板/周报」重生成。

**权威契约**：`references/visualization-reference.md`（完整 DATA schema、TickTick→视觉映射、渲染流程、模板改造约定）。模板在 `scripts/templates/`：`kanban-colorful.html` / `kanban-claude.html` / `kanban-notion.html` / `weekly-report.html`。下面只给要领，细节看参考文档。

### 看板（"生成看板" / `/task-dashboard`）

1. **问皮肤**（除非用户已指定）：彩色 Colorful / 暖纸 Claude / 纯白 Notion。
2. **拉数据**：`filter_tasks(filter={"status":[0]})` 全量未完成 + `list_projects`（项目名/色）+ 今日 `list_completed_tasks_by_date`（算 completedToday）。
3. **拼 DATA**：按参考文档 §3 算 `today / stats / categories / calendar / focus / timeline / matrix`。关键映射：
   - 四象限：`重要=priority≥3`、`紧急=已过期或今/明天到期` → do / plan / delegate / eliminate。
   - 时间轴：带时刻的任务进 events；**全天任务也进**，放 day 顶部 all-day 横栏 + week 当天列 chip。
   - 今日焦点：过期→今日→高优先，取 ≤4。
4. **注入**：读 `scripts/templates/kanban-<theme>.html`，把 `INJECT_DATA_HERE` 替换成 JSON 字面量。
5. **写出打开**：写到临时 HTML（如 `%TEMP%\ticktick-kanban.html`），`explorer.exe "<路径>"` 或 `cmd /c start "" "<路径>"` 调默认浏览器。
6. 提醒用户：改任务回对话说，再说"刷新看板"重生成。

### 周报（"生成周报" / `/week-report`）

1. **拉数据**：本周完成 `list_completed_tasks_by_date(本周一~今天)` + 下周到期 `list_undone_tasks_by_date(明天~下周日)` + 全量筛过期 + `list_projects`。
2. **草拟文案**（agent 生成、需用户确认的草稿，先贴出来再注入）：
   - `lede` 一句话总结、`top3` 下周重点、`typeBreakdown` 按任务语义归类（功能/Bug/评审…，不依赖标签）。
3. **拼 DATA.report** → 注入 `weekly-report.html` → 写临时文件 → 打开。
4. 提醒：文案可继续改，改完重新生成。

### 注意

- **创建时间可用**：MCP 任务对象带 `createdTime`（ISO `+0000`），需要"本周新增"可按它筛；当前类型分布仍走 agent 语义归类（设计选择，非数据缺口）。
- **Token 过期**：渲染前的 MCP 调用若 401，按上面 MCP Setup 的 Token expiry 重新登录。
- **时区**：所有时间 Asia/Shanghai，ISO 8601 带偏移；相对日期（本周一、下周日）agent 换算成绝对值注入，模板不算。
