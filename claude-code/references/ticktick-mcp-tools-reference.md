# TickTick MCP Tools Quick Reference

All tools are accessed via `mcp_ticktick_*` prefix.

## Task CRUD

| Tool | Required Params | Optional Params |
|------|----------------|-----------------|
| `create_task` | title, project_id | content, start_date, due_date, priority |
| `batch_create_tasks` | tasks (array) | — |
| `create_subtask` | subtask_title, parent_task_id, project_id | content, priority |
| `update_task` | task_id, project_id | title, content, start_date, due_date, priority |
| `complete_task` | project_id, task_id | — |
| `delete_task` | project_id, task_id | — |

## Query Tools

| Tool | Params | Returns |
|------|--------|---------|
| `get_all_tasks` | — | All tasks (ignores closed projects) |
| `get_engaged_tasks` | — | High priority + due today/overdue |
| `get_next_tasks` | — | Medium priority + due tomorrow |
| `get_tasks_due_today` | — | Tasks due today |
| `get_tasks_due_tomorrow` | — | Tasks due tomorrow |
| `get_tasks_due_this_week` | — | Tasks due within 7 days |
| `get_tasks_due_in_days` | days (int) | Tasks due in N days |
| `get_overdue_tasks` | — | Overdue tasks |
| `get_tasks_by_priority` | priority_id (0/1/3/5) | Tasks by priority |
| `search_tasks` | search_term (string) | Tasks matching keyword |
| `get_project_tasks` | project_id | All tasks in project |
| `get_task` | project_id, task_id | Single task details |

## Project Tools

| Tool | Params | Returns |
|------|--------|---------|
| `get_projects` | — | All projects |
| `get_project` | project_id | Project details |
| `create_project` | name | color, view_mode |

## Data Types

- **priority**: `0` (None), `1` (Low), `3` (Medium), `5` (High)
- **dates**: ISO 8601 with timezone, e.g. `2026-05-20T10:00:00+0800`
- **reminders**: Array of `{"trigger": "TRIGGER:P3D"}` (iCal TRIGGER format)
