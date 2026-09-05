# Toutiao Publishing Suite & AI Creative Engine

> **版本**：`v2.1` | **状态**：✅ `Stable` | **最新日复盘**：[2026-09-05.md](docs/daily__pipeline_reviews/2026-09-05.md)

Toutiao Publishing Suite 是一个基于 **Playwright / Patchright** 的工业级自动化创作与发布套件。它不仅实现了头条创作者中心及其 ProseMirror 富文本编辑器的精准注入与持久化免登发布，更贯通了从热点灵感嗅探、Stanford STORM 多视角深度调研、AI 腔质检硬性断言、16:9 高清插图生成到 AntiGravity 原生定时任务唤醒的全生命周期自动化闭环。

---

## 1. 架构原理 (Architecture)

套件严格遵循 **"模拟真实用户行为" (User Simulation)** 与 **"D 盘沙箱化隔离" (Sandbox Isolation)** 原则，彻底杜绝 C 盘临时文件污染。

### 1.1 核心全链路流程

```
平台热点与任务 (scout_trends.py)
           │
           ▼
多视角深度调研 (research_engine.py / STORM 4 视角)
           │
           ▼
正文起草与质检 (pipeline.py / ContentAuditor 抗AI腔断言)
           │
           ▼
富文本与排版编译 (md2html.py / 话题标签正规化)
           │
           ▼
浏览器工厂与发文 (publisher.py + auth_manager.py + browser_utils.py)
           │
           ▼
定时任务日常提醒 (manage.py radar / AntiGravity Scheduled Tasks)
```

### 1.2 核心组件功能一览

*   **`manage.py` (统一管理 CLI 入口)**：提供 `setup`、`status`、`radar`、`scout`、`research`、`audit`、`draft`、`publish`、`list` 等一站式子命令。
*   **`scripts/publisher.py` (发布核心执行器)**：
    *   针对 ProseMirror 编辑器，采用多级降级策略（`execCommand` > `ClipboardEvent`）实现内容无损灌入。
    *   支持正文多图相对路径解析与剪贴板自动上传。
    *   具备**封面空插槽自愈机制**（正文无图或未自动拾取时，自动上传本地同目录 `cover.jpg`）。
    *   具备**手机端预览弹窗 JS 穿透终审**，彻底解决遮罩层拦截合成点击事件导致超时的顽疾。
*   **`scripts/auth_manager.py` (凭证与免登管理)**：
    *   负责 Cookie 与 LocalStorage 在 D 盘 `.data/browser_state/state.json` 的持久化与在线验证（`--verify`）。
*   **`scripts/browser_utils.py` (浏览器工厂)**：
    *   集成 Win32 API 焦点穿透（`AttachThreadInput` + `SetForegroundWindow`），防止后台静默启动导致假阳性运行。
    *   启动与退出时自动重置崩溃恢复气泡标记（`exit_type: Normal`）。
*   **`scripts/research_engine.py` (深度调研与选题生成引擎)**：
    *   借鉴 Stanford STORM 与阿里 DeepResearch 架构，执行 4 维多视角拆解（经济民生账本、心理情感边界、代际观念反差、反常识底层洞察）。
    *   生成高 CTR 结构化方案卡片、黄金抓人导语及 16:9 配图提示词，沉淀事实账本至 `output/research_dossier.md`。
*   **`scripts/scout_trends.py` & `scripts/daily_scout.py` (热点与灵感雷达)**：
    *   爬取头条后台创作灵感与热门话题，过滤互动游戏类低质内容，结合热度权重输出精选推荐。
*   **`scripts/pipeline.py` (质检审计与协同管线)**：
    *   内置 `ContentAuditor`：字数严格控制在 480-620 纯汉字区间；标题若承诺数字（如“三点”、“九个字”），正文论证必须形成严密闭环；命中 AI 腔套话黑名单直接拦截。
*   **`scripts/md2html.py` (编译器与排版正规化)**：
    *   `normalize_topics` 预处理器阻断文末 `#话题#` 编译为 `<h1>`/`<h2>` 触发头条红杠大标题样式，升级正则为 `re.compile(r"^#[^#\s
]+#")`，完美支持含逗号、问号等标点的话题标签。

---

## 2. 快速启动指南 (Quick Start)

### 2.1 环境准备

- 操作系统：Windows 10/11
- Python 版本：Python 3.11+
- 核心依赖：Playwright / Patchright、Markdown、pytest

```powershell
# 1. 首次初始化与扫码登录（Win32 穿透置顶全屏弹出）
python manage.py setup

# 2. 校验登录态是否在线有效
python manage.py status --verify

# 3. 运行完整测试套件（52 项单测全部通过）
python -m pytest
```

### 2.2 核心操作命令

```powershell
# 运行每日选题雷达（爬取灵感 -> 深度调研 -> 生成 3~5 套精选方案卡片）
python manage.py radar

# 将本地文章注入头条创作者中心草稿箱（等待 5 秒保存后自动退出）
python manage.py draft -f articles/sample_article.md --wait 5

# 正式发布文章至头条号（正文、配图、首发声明、广告收益与文末话题全自动）
python manage.py publish -f articles/09/05/连广州这些老字号都撑不住了_普通人挣钱有多难/连广州这些老字号都撑不住了_普通人挣钱有多难.md

# 查看创作者后台已发布文章或草稿箱列表
python manage.py list
python manage.py list --tab draft
```

---

## 3. 目录架构 (File Tree)

```
10-Toutiao/
├── manage.py                   # 统一管理 CLI 入口
├── requirements.txt            # 项目依赖清单
├── SKILL.md                    # Antigravity Agent Skill 规范定义
├── ReadMe.md                   # 架构说明与版本日志（Zone A + Zone B）
├── Handover Book.md            # 项目交接账本与决策档案（Zone A/B/C）
├── articles/                   # 正式产出归档目录（按 articles/MM/DD/篇名/ 存储）
│   ├── 09/04/                  # 9月4日发文（《带孩子“见世面”》）
│   └── 09/05/                  # 9月5日发文（《连广州老字号》《老了什么是你的底气》《年少吃苦老来吃苦》《取消英语主科》）
├── docs/
│   ├── daily__pipeline_reviews/# 每日流水线闭环复盘（如 2026-09-05.md）
│   └── project-state/          # 下一会话恢复卡（RESUME.md）
├── scripts/                    # 核心脚本库
│   ├── publisher.py            # 发布执行器（ProseMirror 注入与事件触发）
│   ├── auth_manager.py         # 认证状态管理与在线探活
│   ├── browser_utils.py        # 浏览器工厂（Win32 焦点穿透与崩溃重置）
│   ├── scout_trends.py         # 头条热点与创作灵感嗅探
│   ├── daily_scout.py          # 每日雷达调度器
│   ├── research_engine.py      # STORM 4 视角深度调研引擎
│   ├── pipeline.py             # 质检审计器与协同编排
│   ├── md2html.py              # Markdown 排版转富文本编译器
│   ├── fetch_articles.py       # 文章/草稿箱拉取
│   ├── config.py               # 路径沙箱化与常量配置
│   ├── run.py                  # 运行兼容适配层
│   └── setup_environment.py    # 虚拟环境与依赖管理
└── tests/                      # 单元测试套件（52 项用例）
```

---

## 4. 当前运行状态 (Current Status)

- **发文实测**：已在头条号实测正式上线 4 篇图文并茂长文，排在作品列表第 1 位；草稿箱成功留存 1 篇。
- **定时调度**：已挂载 AntiGravity 原生 Scheduled Tasks（Task ID `task-1210`），每日固定 09:00 与 15:00 自动唤醒并推送 3~5 套精选题卡。
- **测试通过率**：`python -m pytest` 共 52 项测试用例全部通过（50 passed，2 skipped）。

---

## Zone B — Changelog Ledger

### [v2.1] — 2026-09-05 22:30 | Session: S-20260905-2230
**Summary**: 项目全量深度审查与工程优化：修复封面空插槽自愈逻辑退化，修正文章自动建目录格式与单测补齐，消除全库裸 except 与未用依赖，同步全套文档与发文资产。
**Changes**:
- 🐛 Fixed: `scripts/publisher.py` 恢复封面空插槽非空检查（`article-cover-add`）自愈逻辑，阻断富文本未能自动提取正文图时的发布拦截。
- 🐛 Fixed: `scripts/pipeline.py` 修正 `prepare_article_directory` 中的月份目录格式为标准 `MM/DD`，增加 `base_dir` 测试隔离支持。
- 🧪 Tests: `tests/test_pipeline.py` 扩充 `test_prepare_article_directory_structure` 目录结构与附件拷贝单测，测试套件扩增至 52 项（50 passed, 2 skipped）。
- ♻️ Refactor: 修复 `browser_utils.py` 与 `publisher.py` 中的裸 `except:`，清理全仓库 8 处 unused imports 与冗余 f-strings。
- 📄 Docs: 同步更新 `ReadMe.md`、`Handover Book.md`、`RESUME.md` 与 `docs/daily__pipeline_reviews/2026-09-05.md`，录入第 4 篇发文《取消英语主科，无异于自断一臂》。
**Context**: 响应用户对项目进行全面审查并实施必要优化修复的指令。

### [v2.0] — 2026-09-05 14:15 | Session: S-20260905-1415
**Summary**: 重大里程碑升级：从单点发文脚本全面演进为集热点嗅探雷达、STORM 深度调研、抗 AI 质检审计、封面自愈上传与定时调度于一体的头条全链路创作发布套件。
**Changes**:
- ✨ Added: `scripts/scout_trends.py` & `scripts/daily_scout.py`，无头爬取头条创作者中心热门灵感话题与瓜分奖金任务。
- ✨ Added: `scripts/research_engine.py`，落地 Stanford STORM 4 视角启发式调研，生成多维度事实账本与创作方案。
- ✨ Added: `scripts/pipeline.py`，内置 `ContentAuditor` 发文前严格校验 480-620 字数、数字逻辑闭环与 AI 腔拦截。
- ✨ Added: AntiGravity 官方原生 Scheduled Tasks 调度支持（Task ID `task-1210`，`0 9,15 * * *`）。
- ♻️ Modified: `scripts/md2html.py` 升级话题标签正规化编译器，防止文末标签被错误编译为大标题红杠，完美兼容标点符号。
- 🐛 Fixed: `scripts/publisher.py` 增加封面空插槽自动上传 `cover.jpg` 与原生 JS 穿透点击手机预览“确认发布”按钮。
- 🧪 Tests: 单测套件大幅扩充至 51 项（新增 `test_scout_trends.py`、`test_research_engine.py`、`test_pipeline.py`）。
- 📄 Docs: 建立 `docs/daily__pipeline_reviews/2026-09-05.md` 与 `docs/project-state/RESUME.md` 规范。
**Context**: 响应用户对更宽广文章思路来源、热点灵感嗅探、深度调研推演及自动化定时推送的全流程体系化需求。
