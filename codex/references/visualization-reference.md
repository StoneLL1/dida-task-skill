# 可视化参考 · DATA Schema 与渲染契约

本文件是 **agent 与 HTML 模板之间的唯一契约**。agent 负责从 TickTick 拉数据、按本文规则拼成单个 `DATA` JSON，注入模板；模板只读 `DATA` 渲染，不联网、不写回 TickTick。

共四个模板（位于 `scripts/templates/`）：
- `kanban-colorful.html` / `kanban-claude.html` / `kanban-notion.html` — 任务看板（同一信息架构，三套皮肤）
- `weekly-report.html` — 周报

看板与周报共用同一个 `DATA` 对象，各取所需字段。

---

## 1. 注入点

每个模板里都有一行：

```html
<script>const DATA = INJECT_DATA_HERE;</script>
```

agent 生成时：读模板文本 → 把 `INJECT_DATA_HERE` 替换为真实 JSON 字面量（不是字符串）→ 写到临时 HTML → 用浏览器打开。替换后应为：

```html
<script>const DATA = { "generatedAt": "...", ... };</script>
```

> 注意：JSON 里若含 `</script>` 片段需转义为 `<\/script>`。一般任务数据不会出现。

---

## 2. 完整 DATA Schema

```jsonc
{
  "generatedAt": "2026-07-14T17:30:00+0800",   // 页面生成时刻（ISO 8601 带偏移）
  "user": "StoneLL1",                          // 显示名（可空）
  "view": "kanban",                            // "kanban" | "weekly"
  "theme": "colorful",                         // 仅看板：colorful | claude | notion

  // —— 日期上下文（agent 算好注入；模板不算"今天/本周"）——
  "today": {
    "iso": "2026-07-14",
    "y": 2026, "m": 7, "d": 14,
    "dow": 2,                                  // 周一=1 … 周日=7
    "dowName": "周二",
    "weekNum": 29,                             // ISO 周序号
    "label": "7月14日 · 周二",                  // 顶栏用
    "monthLabel": "2026 年 7 月"                // 迷你日历头
  },

  // —— 顶部 KPI / 侧栏统计（看板用）——
  "stats": {
    "total": 17,                               // 全部未完成
    "overdue": 1,                              // 过期未完成
    "today": 7,                                // 今日到期
    "thisWeek": 23,                            // 今日起 7 天内到期
    "completedToday": 4                        // 今日已完成
  },

  // —— 侧栏分类（按项目归并；color 取项目色，无项目归"收件箱"）——
  "categories": [
    {"name": "工作", "color": "#391c57", "count": 8},
    {"name": "个人", "color": "#2a9d99", "count": 3}
  ],

  // —— 迷你日历：当前月每天「未完成任务到期数」（0 不出现）——
  "calendar": {
    "year": 2026, "month": 7,
    "todayD": 14,                              // 当月今日日期（用于高亮；跨月时可能不在本月）
    "days": [ {"d": 3, "count": 2}, {"d": 14, "count": 7} ]
  },

  // —— 今日焦点（最多 4；已按 过期 → 今日到期 → 高优先 排序）——
  "focus": [
    {
      "id": "t1",
      "title": "整理本周项目周报",
      "time": "09:00",                         // 开始/到期时刻；全天任务给 "全天"
      "project": "工作",
      "projectColor": "#391c57",
      "priority": 5,                           // 0/1/3/5
      "dueLabel": "今日",                       // 友好截止标签：今日/明日/周五/7-20/逾期2天
      "done": false                            // 是否已完成（恢复勾选用）
    }
  ],

  // —— 时间轴（全天任务也进时间轴）——
  "timeline": {
    "day": {
      "date": "2026-07-14",
      "allDay": [                              // 今日全天任务（无具体时刻）
        {"id": "t9", "title": "全天任务标题", "projectColor": "#391c57"}
      ],
      "events": [                              // 今日带时刻的任务
        {"id": "t1", "title": "整理周报", "start": "09:00", "end": "10:30", "projectColor": "#391c57"}
      ]
    },
    "week": [                                  // 本周周一…周日，7 天
      {
        "date": "2026-07-13", "dow": "周一", "isToday": false,
        "allDay": [],
        "events": [ {"time": "10:00", "title": "需求评审", "projectColor": "#391c57"} ]
      }
    ]
  },

  // —— 四象限（agent 已分桶；quad ∈ do|plan|delegate|eliminate）——
  "matrix": [
    {"id": "t2", "title": "修复登录页 bug", "quad": "do", "priority": 5, "dueLabel": "今日"}
  ],

  // —— 周报专用 ——
  "report": {
    "rangeStart": "2026-07-07",                 // 本周一
    "rangeEnd":   "2026-07-13",                 // 本周日（或今天，看生成时机）
    "rangeLabel": "2026.07.07 — 07.13",
    "issue": 29,                               // 第几期（可由周序号推）
    "submitter": "StoneLL1",                   // 提交人

    "metrics": {
      "done": 12,                              // 本周完成
      "wip": 5,                                // 当前进行中（未完成且未过期）
      "blocked": 2,                            // 过期未完成
      "rate": 86                               // 完成率% = done / (done + wip + blocked)，四舍五入
    },

    "lede": "本周完成 X 并灰度上线……；遗留阻塞集中在 Y，下周优先攻坚。",
    // ↑ agent 读 completed + overdue 自动草拟的一句话总结，1~2 句

    "typeBreakdown": [                         // agent 按任务语义归类（非依赖标签）
      {"name": "功能开发", "count": 5},
      {"name": "Bug 修复", "count": 3},
      {"name": "代码评审", "count": 2}
    ],

    "top3": [                                  // agent 从 upcoming + overdue 草拟下周重点
      {"title": "攻克第三方鉴权阻塞", "plan": "完成对接与联调，解除 P0 阻塞。"}
    ],

    "completed": [                             // 本周完成清单 → 渲染为 §05「本周完成」
      {"id":"c1","title":"搜索结果页重构","project":"工作","projectColor":"#391c57","priority":5,"completedLabel":"周二 14:30"}
    ],
    "upcoming": [                              // 下周到期的未完成 → 渲染为 §07「下周到期」
      {"id":"u1","title":"设计评审","dueLabel":"周一","project":"工作","projectColor":"#391c57","priority":3}
    ],
    "overdue": [                               // 当前过期未完成 → 渲染为 §06「过期阻塞」（行带 .warn，meta 用 cobalt 色）
      {"id":"o1","title":"第三方鉴权联调","dueLabel":"逾期 3 天","overdueDays":3,"project":"工作","projectColor":"#391c57"}
    ],
    "byProject": [                             // ⚠ 当前模板未单独渲染（类型分布已由 typeBreakdown 覆盖）；字段保留备用
      {"name":"工作","count":5,"color":"#391c57"}
    ]
  }
}
```

---

## 3. TickTick → 视觉 映射规则（agent 端计算）

### 3.1 四象限 `matrix[].quad`

二分两个轴：

- **重要 (important)** = `priority ≥ 3`（中或高）
- **紧急 (urgent)** = `overdue`（dueDate < 今天 00:00）**或** dueDate 落在**今天/明天**

| quad | 判定 |
|---|---|
| `do`（立即做） | 重要 & 紧急 |
| `plan`（计划） | 重要 & 不紧急 |
| `delegate`（委派） | 不重要 & 紧急 |
| `eliminate`（减少） | 不重要 & 不紧急 |

> 无 dueDate 的任务视为「不紧急」。象限内按 priority 降序、再按 dueDate 升序排。
> 每个象限封顶 50 条；超出在象限底部注明「共 N 条，显示前 50」。

### 3.2 时间轴 `timeline`（全天任务也进）

- **带时刻的任务** → `events`：`start`/`end` 取 `startDate`/`dueDate` 的 HH:MM。只有单个时刻时，`end` 留空，渲染为短块。
- **全天任务**（`isAllDay=true`，或 dueDate 为纯日期无时刻）→ `allDay`：无具体小时，渲染为日视图顶部的「全天」横栏、周视图当天列的全天 chip。
- **周视图**：遍历本周周一~周日，把当天的 allDay + events 归到对应列。
- 时间轴默认时段 08:00–22:00；落在区间外的事件夹到边界并标注真实时刻。

### 3.3 今日焦点 `focus`（≤4 条）

从「今日到期 + 过期」里取，排序：过期优先 → 今日到期 → priority 降序。`time` 取开始/到期时刻，全天给 `"全天"`。

### 3.4 迷你日历 `calendar.days`

当月每天「未完成任务到期数」→ `count > 0` 才出现。点上去不做跳转（只读快照）。

### 3.5 周报文案草拟（`lede` / `top3` / `typeBreakdown`）

- `typeBreakdown`：agent 读本周 `completed` 每条标题/正文，**语义归类**到若干桶（如 功能开发 / Bug 修复 / 代码评审 / 文档规范 / 沟通会议 / 其他）。条数从高到低排。
- `lede`：基于本周完成亮点 + 过期阻塞，草拟 1~2 句中文总结。
- `top3`：从 `upcoming` + `overdue` 里挑下周最该推进的 3 件，各写一句 plan。
- 三者均为**草稿**，生成后 agent 应在对话里把文案贴给用户确认/修改，再注入。

---

## 4. 数据来源（MCP 调用对照）

| 用途 | 调用 | 备注 |
|---|---|---|
| 看板全量任务 | `filter_tasks(filter={"status":[0]})` | 一次拉全，agent 端分桶/统计 |
| 看板项目色/名 | `list_projects` | 建 projectId → {name,color} 映射 |
| 周报 · 本周完成 | `list_completed_tasks_by_date(search={"startDate":本周一,"endDate":今天})` | |
| 周报 · 下周到期 | `list_undone_tasks_by_date(search={"startDate":明天,"endDate":下周日})` | ≤14 天 |
| 周报 · 过期/积压 | 复用 `filter_tasks(status:[0])` 筛 dueDate < 今天 | |
| 今日已完成 | `list_completed_tasks_by_date` 今天 | KPI `completedToday` |

> **创建时间可用**：MCP 任务对象带 `createdTime`（ISO 8601，`+0000`）。如需"本周新增"可直接按 `createdTime` 落在本周范围内筛。当前周报的"任务类型分布"仍按 agent **语义归类**（功能/Bug/评审…），不依赖标签——这是设计选择，并非数据缺口。

---

## 5. 模板统一改造契约（4 份都遵守）

每份模板相对用户原始设计 HTML 的改造：

1. **CSS 一字不改**保留。
2. **加注入点**：在主交互 `<script>` 之前插入 `<script>const DATA = INJECT_DATA_HERE;</script>`。
3. **删演示数据**：把写死的（李明 / PRD v2 / 14:30 / 周一13…）移除，留空容器并加 `id`，如 `#focus-row`、`#tl-track`、`#quad-do .q-list`、`#minical`、`#stat-today` 等。
4. **写 `render(DATA)`**：按 DATA 重建上述容器。渲染完再调用交互绑定。
5. **交互全部保留**并在 `render` 后重新绑定（因为 DOM 是动态生成的）：
   - 日/周切换、迷你日历切换月份、勾选完成、进度环（Colorful）、新建任务、四象限拖拽、localStorage 持久化（Notion）、键盘快捷键（N/D/W）。
6. **顶部加横幅**：醒目但不抢戏的一条 `本地预览 · 不同步滴答清单，改动请回对话同步`。新建/勾选/拖拽等操作触发的弹窗或提示里也复述一句"不会同步"。
7. **「现在」指示线**按真实当前时间定位（`new Date()`），落在时间轴时段外则隐藏。原设计里写死的 14:30 删掉。
8. **时间轴加「全天」横栏**：日视图时段网格上方一条全天任务带；周视图当天列也渲染全天 chip。
9. **空状态**：任一区块数据为空显示一句"暂无"，不留大白块；整页无任务显示"🎉 没有未完成任务"。
10. **截断**：任一列表 >100 条只渲染前 100，底部注"显示前 100 条，共 N 条"。

---

## 6. 渲染流程（agent 执行步骤）

**看板**（用户说"生成看板"或 `/task-dashboard`）：

1. **问皮肤**：彩色(Colorful) / 暖纸(Claude) / 纯白(Notion) —— 除非用户已指定。
2. **拉数据**：`filter_tasks(status:[0])` + `list_projects`；补今日 completed 给 KPI。
3. **拼 DATA**：按第 3 节规则算 stats / categories / calendar / focus / timeline / matrix。
4. **注入**：读 `scripts/templates/kanban-<theme>.html`，替换 `INJECT_DATA_HERE`。
5. **写文件**：写到临时路径（如 `%TEMP%\ticktick-kanban.html` 或固定输出路径）。
6. **打开**：Windows 用 `explorer.exe "<路径>"` 或 `cmd /c start "" "<路径>"` 调默认浏览器。
7. 改任务回对话说 → agent 调 MCP 改 → 用户说"刷新看板"→ 重生成。

**周报**（用户说"生成周报"或 `/week-report`）：

1. **拉数据**：本周 completed + 下周 undone + 全量筛 overdue + projects。
2. **草拟文案**：lede / top3 / typeBreakdown，贴给用户确认。
3. **拼 DATA.report** → 注入 `weekly-report.html` → 写文件 → 打开。

---

## 7. 一致性约定

- **时区**：所有时间本地时区（Asia/Shanghai），ISO 8601 带偏移。相对日期（本周一、下周日）由 agent 换算成绝对值注入，模板不算。
- **优先级配色**（建议，各皮肤可微调以贴合自身调性）：高(5)=红 · 中(3)=橙/琥珀 · 低(1)=蓝 · 无(0)=灰。
- **项目色**：直接用 TickTick 项目 `color` 字段（hex）。

---

## 8. 已知限制

- **子任务（parent/child）扁平渲染**：TickTick 任务带 `parentId` / `childIds`，可构成父子关系。当前 4 份模板的 DATA schema（`matrix` / `focus` / `timeline` / `report.*`）都是扁平任务列表，**不表达层级**——父子任务各自作为独立条目渲染，不缩进、不折叠、不显示归属。这不是崩溃性 bug（实测有父任务 + 2 个子任务时正常铺平显示），但视觉上看不出归属关系。如需层级展示，后续可给任务对象加 `parentId` / `depth` 字段并在模板里缩进渲染。
- **周报 `byProject` 字段未渲染**：schema 保留了该字段（见 §2），但模板未画对应区块——按项目归并的分布信息已由 `typeBreakdown`（语义归类）覆盖。字段保留供后续。
- **交互不同步**：看板内的勾选 / 拖拽 / 新建均为本地预览（顶部横幅已注明「本地预览 · 不同步」），不写回 TickTick。真正改任务需回对话用 MCP 工具操作，再「刷新看板 / 周报」重生成。
