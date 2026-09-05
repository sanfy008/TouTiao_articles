---
name: toutiao-publisher
description: |
  今日头条（Toutiao/头条号）全生命周期 AI 创作与自动化发文专家技能。
  涵盖：创作者后台热门灵感与瓜分奖金任务嗅探（`scout_trends` / `daily_scout`）、Stanford STORM 4 视角深度调研（`research_engine`：经济账本/心理边界/代际反差/底层洞察）、抗 AI 腔与数字逻辑闭环质检审计（`pipeline.py` / `ContentAuditor`）、16:9 高清配图合成、ProseMirror 话题标签防红杠正规化编译（`md2html.py`）、D 盘沙箱化免登会话持久化、Win32 穿透置顶、封面自愈上传与移动端预览原生 JS 穿透终审发布（`publisher.py`），以及 AntiGravity 原生 Scheduled Tasks 每日定点自动唤醒调度。
  触发场景：头条发文、头条选题、热点嗅探、创作灵感、抗AI腔质检、头条草稿填充、头条自动发布、免登录验证、定时选题雷达。
---

# Toutiao Creative & Publishing Suite (今日头条全生命周期创作与发文套件)

## 1. 角色定位与设计哲学

本 Skill 将今日头条的运营发布从“单点浏览器灌入脚本”提升为**“全链路工业级内容生产线”**。
遵循三大铁律：
1. **D 盘沙箱隔离（Zero C-Drive Pollution）**：浏览器配置、Cookie、临时文件严格锁定于 D 盘项目沙箱，严禁污染宿主机 C 盘。
2. **抗 AI 腔与逻辑闭环（Anti-AI Platitudes & Logical Closure）**：正文严格控制在 480-620 纯汉字区间；标题若承诺数字（如“三点”、“九个字”），正文论证必须形成严密闭环，禁止空洞套话。
3. **真实用户仿真与双轨防线（User Simulation & Resilient Fallbacks）**：ProseMirror 富文本注入、Win32 焦点穿透、封面空插槽自愈、手机预览弹窗原生 JS 穿透，确保 100% 发布成功率。

---

## 2. 全生命周期流水线架构

```
[Phase 1] 热点与创作灵感嗅探 (scout_trends.py / manage.py radar)
    │
    ▼
[Phase 2] Stanford STORM 4 视角深度调研 (research_engine.py)
    │   ├─ 视角 A: 经济民生真实账本（柴米油盐、沉没成本、边际收益）
    │   ├─ 视角 B: 心理情感隐秘边界（自尊防御、隐秘内疚、安全感转移）
    │   ├─ 视角 C: 代际观念断层反差（父辈执念、当下青年、现实碰撞）
    │   └─ 视角 D: 反常识底层逻辑洞察（戳破伪命题、去鸡汤化本质）
    │
    ▼
[Phase 3] 深度起草与抗 AI 腔质检 (pipeline.py / ContentAuditor)
    │   ├─ 严格字数区间断言：480 ~ 620 纯汉字
    │   ├─ 承诺数字严密闭环：标题与结论数字逻辑 1:1 吻合
    │   └─ AI 套话黑名单过滤：拒绝“值得我们深思/在当今快节奏/总而言之”
    │
    ▼
[Phase 4] 富文本编译与排版正规化 (md2html.py / normalize_topics)
    │   └─ 话题标签拦截：阻断文末标签编译为大标题红杠，正规化为纯净正文 <p>
    │
    ▼
[Phase 5] 免登会话持久化与发文 (publisher.py + auth_manager.py + browser_utils.py)
    │   ├─ Win32 原生置顶穿透（AttachThreadInput + SetForegroundWindow）
    │   ├─ 封面空插槽自愈回退上传（自动补齐同目录 cover.jpg）
    │   └─ 移动端预览弹窗原生 JS 穿透确认发布
    │
    ▼
[Phase 6] 每日定点自动唤醒调度 (AntiGravity Scheduled Tasks / task-1210)
        └─ 每日 09:00 与 15:00 自动触发 manage.py radar 推送精选选题卡片
```

---

## 3. 统一管理 CLI 速查手册 (`manage.py`)

所有操作均收敛于项目根目录的 `manage.py` 入口：

### 3.1 身份认证与环境校验
```powershell
# 首次扫码登录（Win32 穿透前台全屏弹出，生成 D 盘持久化 state.json）
python manage.py setup

# 验证登录态是否在线有效（访问头条受保护页面在线探活）
python manage.py status --verify

# 运行完整自动化测试套件（51 项单测全部绿灯）
python -m pytest
```

### 3.2 选题嗅探与深度调研
```powershell
# 运行每日热点与灵感雷达（嗅探头条后台 -> 深度调研 -> 生成 3~5 套精选卡片）
python manage.py radar

# 单独嗅探创作者后台热门灵感与瓜分奖金任务
python manage.py scout

# 对特定社会现象或命题发起 STORM 4 视角深度调研
python manage.py research "老了什么是你的底气"
```

### 3.3 质检与发文执行
```powershell
# 发文前严性质检审计（字数 480-620、承诺数字闭环、抗AI腔黑名单）
python manage.py audit -f articles/09/05/连广州这些老字号都撑不住了_普通人挣钱有多难/连广州这些老字号都撑不住了_普通人挣钱有多难.md

# 灌入头条草稿箱并停留 5 秒供人工审核（安全默认）
python manage.py draft -f articles/sample_article.md --wait 5

# 正式发布文章至头条号（需用户显式授权，自动执行声明、配图、广告与话题）
python manage.py publish -f articles/09/05/连广州这些老字号都撑不住了_普通人挣钱有多难/连广州这些老字号都撑不住了_普通人挣钱有多难.md

# 查看创作者后台已发布文章或草稿箱列表
python manage.py list
python manage.py list --tab draft
```

---

## 4. Subagents 协同分工规范 (Multi-Agent Protocol)

当用户选定某一选题方案后，流水线按如下分工指派 subagents 协同作业：

| 阶段 / Subagent 角色 | 核心职责 | 输入与输出 | 质量验收标准 (Gate) |
|---|---|---|---|
| **1. 调研员 (Researcher)** | 执行 Stanford STORM 4 视角拆解 | 输入选题，输出 `output/research_dossier.md` | 必须具备明确的利益冲突与反常识洞察 |
| **2. 主笔 (Writer)** | 撰写生活哲理/社会观察短文 | 基于调研事实撰写，控制 500 字左右 | 严禁空洞鸡汤，段落短促有力 |
| **3. 审计员 (Auditor)** | 执行 `ContentAuditor` 硬性质检 | 审查字数、数字闭环与 AI 腔 | 纯汉字 480-620 字；承诺数字逻辑 100% 闭环 |
| **4. 视觉师 (Designer)** | 生成 16:9 高清写实插图与封面 | 提取黄金场景生成提示词并产出 JPG | 画面接地气、具有生活烟火气与情感共鸣 |
| **5. 排版师 (Typesetter)** | 转换为头条专用富文本 HTML | 剥离 Frontmatter，正规化话题标签 | 严禁文末标签渲染为大标题红杠 |
| **6. 发行员 (Publisher)** | 调用 `publisher.py` 执行发文 | 自动填充、传图、勾选声明、点击终审 | 必须校验平台成功跳转（`/manage/content`） |

---

## 5. 防错规则与核心防线 ([FAIL 防线])

- `[FAIL-001 防线]` **Win32 原生置顶穿透**：严禁仅以 CDP 连通性或 `page.bring_to_front()` 推断窗口可见性；在 Windows 宿主机上必须通过 `user32.dll` 注入与 `AttachThreadInput` 穿透前台锁。
- `[FAIL-002 防线]` **话题标签正规化**：严禁在文末输出裸 `#话题#`；必须经 `md2html.py` 中 `normalize_topics` 预处理器转换为 `<p>#标签#</p>`，且正则必须兼容逗号、问号等复杂标点（`re.compile(r"^#[^#\s
]+#")`）。
- `[FAIL-003 防线]` **双轨极速发文终审**：手机预览弹窗具有动画遮罩，常规点击超时前必须无缝切换为原生 JS `button.click()` 穿透点击；正文有图时若封面插槽为空，必须自愈上传本地 `cover.jpg`。
- `[FAIL-004 防线]` **资产与技能契约闭环**：在新增功能、重构流水线或执行 `project-save` 时，必须同步审查并更新项目根目录的 `SKILL.md`，确保技能契约与底层代码资产严格对齐。

---

## 6. 系统级定时调度机制 (Scheduled Tasks)

已集成 AntiGravity 原生 Scheduled Tasks 调度系统（Task ID `task-1210`）：
- **周期**：`0 9,15 * * *`（每日 09:00 与 15:00 准时唤醒）
- **动作**：自动执行 `python manage.py radar`，完成热点与灵感爬取、STORM 深度调研，并在对话流中直接呈现 3~5 套高品质创作方案卡片供用户决策。
