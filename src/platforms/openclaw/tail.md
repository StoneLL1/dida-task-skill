## Common Scenarios

| Scenario | Action |
|----------|--------|
| "帮我创建一个任务" | Parse info, create directly. Ask if title missing. |
| User forwards notification text | Apply notification parsing template |
| "提醒我明天下午3点开会" | title="开会", start_date=tomorrow 15:00 |
| "把这条加到滴答清单" + text | Apply notification parsing template |
| "我有什么待办" | `list_undone_tasks_by_time_query("today")` + `list_undone_tasks_by_time_query("tomorrow")` |

## Verification Checklist

After creating a task, verify:
- [ ] Title is concise and actionable (not raw notification text)
- [ ] Due date matches user intent (not fabricated)
- [ ] Priority aligns with urgency rules above
- [ ] Project matches routing logic
- [ ] No duplicate exists（`filter_tasks(status:[0])` + 标题比对已查；`search` 不可靠，别用）
- [ ] Response format is the one-line confirmation
