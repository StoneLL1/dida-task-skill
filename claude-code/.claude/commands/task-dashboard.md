---
description: 生成 TickTick 任务看板（日程仪表盘）
---

使用 **ticktick-task** skill 的可视化能力生成任务看板。严格按 `references/visualization-reference.md` 的渲染流程执行。

步骤：
1. **皮肤**：若下面 `$ARGUMENTS` 给了皮肤名（彩色/colorful、暖纸/claude、纯白/notion），直接用；否则先问我选哪套，再继续。
2. **拉数据**：`filter_tasks(filter={"status":[0]})` 拉全部未完成 + `list_projects` 取项目名/色；补今日 `list_completed_tasks_by_date` 给 KPI 的 completedToday。
3. **拼 DATA**：按文档 §3 映射规则算 `stats / categories / calendar / focus / timeline(含全天) / matrix`，并填 `today` 上下文。
4. **注入**：读 `scripts/templates/kanban-<theme>.html`，把 `INJECT_DATA_HERE` 替换为真实 JSON 字面量。
5. **写出打开**：写到临时 HTML（如 `%TEMP%\ticktick-kanban.html`），用 `explorer.exe "<路径>"` 或 `cmd /c start "" "<路径>"` 打开默认浏览器。
6. 告诉我已打开，提示「改任务回对话说，再说『刷新看板』重生成」。

$ARGUMENTS
