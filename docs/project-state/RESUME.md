---
updated: 2026-09-05T22:30:00+08:00
session: S-20260905-2230
project_version: v2.1
status: active
evidence_level: runtime-validated
---

# Resume Card

## Current Contract
- Goal: 构建并维护工业级稳定、零 C 盘污染、全生命周期闭环的今日头条自动化创作与发文套件（含选题雷达、STORM 调研、AI 腔质检断言、配图合成、ProseMirror 富文本注入与定时提醒）。
- Scope / non-goals: 当前聚焦于 500-1500 字深度图文长文章；暂不覆盖微头条短动态批量发布与视频剪辑上传。
- Constraints: 严禁 C 盘数据写入；正文严格控制 480-620 字区间；承诺数字必须形成严密逻辑闭环；严禁 AI 腔套话与占位符；文末话题标签不得编译为大标题。
- Acceptance check: `python -m pytest` 全 52 项测试通过；头条创作者中心实测发文上线；AntiGravity 原生定时任务生效；`validate_closure.py` 0 报错。

## Verified State
- [verified] 头条后台免登会话持久化与在线验证 — `scripts/auth_manager.py`、`tests/test_auth_manager.py`
- [verified] Win32 焦点穿透防止 Chrome 假阳性运行 — `scripts/browser_utils.py`、`tests/test_browser_utils.py`
- [verified] 4 篇深度图文长文章成功正式发布至头条号后台排在第 1 位 — `articles/09/04/`、`articles/09/05/`
- [verified] 话题标签标点编译器兼容性与排版防劣化 — `scripts/md2html.py`、`tests/test_md2html.py`
- [verified] 创作灵感热点嗅探雷达与 STANFORD STORM 4 视角调研引擎 — `scripts/scout_trends.py`、`scripts/research_engine.py`、`scripts/daily_scout.py`
- [verified] 封面空插槽自愈补齐与原生 JS 预览终审穿透 — `scripts/publisher.py`、`tests/test_publisher_cover_policy.py`
- [verified] 单测套件扩充至 52 项用例（50 passed，2 skipped） — `tests/`
- [verified] 目录生成规范化至 `articles/MM/DD/` 并新增单测 — `scripts/pipeline.py`、`tests/test_pipeline.py`

## Blockers and Do-Not-Repeat
- [FAIL-001] Windows DWM 焦点隔离导致 Chrome 假阳性运行 — 不得仅凭 CDP 连通性推断浏览器可见性，必须依赖 Win32 原生激活机制。
- [FAIL-002] 话题标签编译为大标题导致头条红杠劣化 — 不得在文末直接输出裸 `#...#`，必须经 `normalize_topics` 预处理转为纯净正文 `<p>` 段落。
- [FAIL-003] 手机预览弹窗遮罩阻断指针导致发文终审超时 — 不得仅依赖 Playwright 单一合成点击，必须配备原生 JS 穿透点击作为强力兜底；若封面插槽为空，必须触发本地封面上传兜底。

## One Next Action
- action: 运行 `python manage.py radar` 检验热点嗅探与 STORM 深度调研卡片生成，静候 AntiGravity 定时触发并由用户拍板下一篇选题。
- completion check: 终端及对话流输出 3~5 套高品质头条创作建议卡片，包含核心冲突、黄金导语及配图构想。

## Read First
- `ReadMe.md`
- `Handover Book.md`
- `docs/daily__pipeline_reviews/2026-09-05.md`
- `scripts/pipeline.py`
