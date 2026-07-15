---
description: 生成 TickTick 本周周报
---

使用 **ticktick-task** skill 的可视化能力生成本周周报。严格按 `references/visualization-reference.md` 的渲染流程执行。

步骤：
1. **拉数据**：
   - 本周完成：`list_completed_tasks_by_date(search={"startDate": 本周一, "endDate": 今天})`
   - 下周到期：`list_undone_tasks_by_date(search={"startDate": 明天, "endDate": 下周日})`
   - 过期未办 + 积压：`filter_tasks(filter={"status":[0]})` 后筛 dueDate < 今天
   - 项目色：`list_projects`
2. **草拟文案**（这是 agent 生成、需我确认的草稿）：
   - `report.lede`：基于本周完成亮点 + 过期阻塞，1~2 句中文。
   - `report.top3`：从 upcoming + overdue 里挑下周最该推进的 3 件，各一句 plan。
   - `report.typeBreakdown`：读本周 completed 每条标题/正文，**语义归类**（功能开发/Bug 修复/代码评审/文档规范/沟通会议/其他），按条数降序。
   - 先把这三段文案贴给我看，我改完确认后再注入。
3. **拼 DATA.report** → 注入 `scripts/templates/weekly-report.html`（替换 `INJECT_DATA_HERE`）。
4. **写出打开**：写到临时 HTML（如 `%TEMP%\ticktick-weekly.html`），用 `explorer.exe` 打开。
5. 提醒：周报文案是草拟的，可继续在对话里改，改完重新生成。

$ARGUMENTS
