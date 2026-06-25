# TickTick (dida365) MCP Tools Reference

Tools are exposed by the remote dida365 MCP server (`https://mcp.dida365.com`).
On Claude Code the tools are named `mcp__dida365__<tool>`; on other runtimes the
prefix differs but the `<tool>` names below are the server's real names. Use
these exact names — older names like `get_engaged_tasks` / `search_tasks` /
`mcp_ticktick_*` are NOT provided by the server.

## Task CRUD

| Tool | Required | Optional | Notes |
|------|----------|----------|-------|
| `create_task` | `task` (object: `title`, `projectId`) | `task.content`, `task.dueDate`, `task.startDate`, `task.priority`, `task.tags`, `task.items` (checklist) | Single task. `priority`: 0/1/3/5. Dates ISO 8601 +tz. |
| `batch_add_tasks` | `tasks` (array of task objects, each needs `title` + `projectId`) | same per-task fields | 3+ tasks in one call. Each task object shape = same as `create_task`'s `task`. |
| `batch_update_tasks` | `tasks` (array, each needs `id` + `projectId`) | per-task fields | Update many. |
| `update_task` | `task_id`, `task` (object with `projectId`) | `task.title`, `task.content`, `task.dueDate`, `task.priority`, etc. | Partial update — send only changed fields. |
| `complete_task` | `project_id`, `task_id` | — | Marks task done. |
| `complete_tasks_in_project` | `project_id`, `task_ids` (array) | — | Batch complete (max 20). |
| `delete_task` | `project_id`, `task_id` | — | |
| `get_task_by_id` | `id` | — | Full task details by ID. |
| `get_task_in_project` | `project_id`, `task_id` | — | Same, scoped to a project. |
| `fetch` | `id` | — | Alias of `get_task_by_id`. |

## Query / Search

| Tool | Required | Returns |
|------|----------|---------|
| `list_undone_tasks_by_time_query` | `query_command` (`today`/`last24hour`/`last7day`/`tomorrow`/`next24hour`/`next7day`) | Undone tasks for that window. **Use this for "what's due / my todos".** |
| `list_undone_tasks_by_date` | `search.startDate`, `search.endDate` (ISO 8601), optional `search.projectIds` | Undone tasks in a date range (max 14 days). |
| `list_completed_tasks_by_date` | `search.startDate`, `search.endDate`, optional `search.projectIds` | Completed tasks in a range. |
| `filter_tasks` | `filter` (object: optional `startDate`/`endDate`/`projectIds`/`priority`/`status`/`tag`/`kind`) | Structured filter. `priority` is an array of 0/1/3/5. |
| `search` | `query` | Tasks matching a keyword (best for dedup). |
| `search_task` | `query` | Same, returns taskId/title/url. |

> The server does **not** provide `get_engaged_tasks`, `get_next_tasks`,
> `get_tasks_due_today`, `get_overdue_tasks`, or `get_tasks_due_this_week`.
> Replace them with `list_undone_tasks_by_time_query` (`today` / `tomorrow` /
> `next7day`) or `filter_tasks`.

## Project Tools

| Tool | Required | Optional |
|------|----------|----------|
| `list_projects` | — | `offset`, `limit` |
| `get_project_by_id` | `project_id` | — |
| `get_project_with_undone_tasks` | `project_id` | — |
| `create_project` | `name` | `color`, `view_mode`, `kind`, `sort_order`, `group_id` |
| `update_project` | `project_id` | `name`, `color`, `view_mode`, `closed`, etc. |
| `list_project_groups` / `create_project_group` / `update_project_group` / `delete_project_group` | see schema | — |
| `list_columns` / `create_column` / `update_column` | `project_id` (+ column obj) | — |

## Move

| Tool | Required | Notes |
|------|----------|-------|
| `move_task` | `moves` (array: `taskId`, `fromProjectId`, `toProjectId`) | Move task between projects. |

## Other (habits, focus, comments, countdowns, preferences)

`list_habits`, `get_habit`, `create_habit`, `update_habit`, `get_habit_checkins`, `upsert_habit_checkins`, `list_habit_sections` · `create_focus`, `get_focus`, `get_focuses_by_time`, `delete_focus` · `add_comment`, `get_comment`, `delete_comment` · `list_countdowns` · `get_user_preference`

These are outside the task-management skill's core flow but are available.

## Data Types

- **priority**: `0` (None), `1` (Low), `3` (Medium), `5` (High)
- **dates**: ISO 8601 with timezone, e.g. `2026-05-20T10:00:00+0800`. To clear a date, send `"1970-01-01T00:00:00.000+0000"`.
- **status**: `0` (active), `-1` (abandoned), `2` (completed)
- **task object** (for create/update): `title`, `projectId`, `content`, `desc`, `dueDate`, `startDate`, `priority`, `tags`, `items` (checklist array), `reminders` (array of `TRIGGER:...` strings), `repeatFlag` (RRULE/ERULE), `isAllDay`, `timeZone`, `kind` (`"TEXT"`/`"NOTE"`/`"CHECKLIST"`)
