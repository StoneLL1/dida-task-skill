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
5. **写出打开**：{{open_html_step}}
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
