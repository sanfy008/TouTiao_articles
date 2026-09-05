#!/usr/bin/env python3
"""
Toutiao Publishing Automation Suite - Unified CLI Entrypoint
头条号自动化发文套件 - 统一管理入口
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path

# Fix Windows console UTF-8 encoding to avoid UnicodeEncodeError on emojis
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).parent.resolve()
TEMP_DIR = PROJECT_ROOT / ".temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)
os.environ["TEMP"] = str(TEMP_DIR)
os.environ["TMP"] = str(TEMP_DIR)
os.environ["PYTHONUTF8"] = "1"

VENV_PYTHON = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
if not VENV_PYTHON.exists():
    VENV_PYTHON = PROJECT_ROOT / ".venv" / "bin" / "python"
if not VENV_PYTHON.exists():
    VENV_PYTHON = Path(sys.executable)


def run_script(script_name: str, args: list):
    """Run a script inside the project environment"""
    script_path = PROJECT_ROOT / "scripts" / script_name
    if not script_path.exists():
        print(f"❌ 找不到脚本: {script_path}")
        return 1

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["TEMP"] = str(TEMP_DIR)
    env["TMP"] = str(TEMP_DIR)

    cmd = [str(VENV_PYTHON), str(script_path)] + args
    return subprocess.call(cmd, env=env)


def cmd_setup(args):
    """唤起专用浏览器完成登录与会话持久化"""
    print("🚀 正在启动今日头条专用持久化浏览器...")
    print("👉 请在弹出的浏览器窗口中完成扫码登录（只需登录一次，后续永久免登）。\n")
    return run_script("auth_manager.py", ["setup"])


def cmd_status(args):
    """检查登录态与有效性"""
    extra_args = ["status"]
    if args.verify:
        extra_args.append("--verify")
    return run_script("auth_manager.py", extra_args)


def cmd_list(args):
    """查看以往历史文章或草稿"""
    list_args = ["--tab", getattr(args, "tab", "published")]
    if args.headed:
        list_args.append("--headed")
    if args.save:
        list_args.append("--save")
    return run_script("fetch_articles.py", list_args)


def extract_title_from_md(file_path: Path) -> str:
    """从 Markdown 文件的 Frontmatter 或首个 H1 提取标题"""
    try:
        content = file_path.read_text(encoding="utf-8")
        lines = content.splitlines()
        
        # 1. 检查 YAML frontmatter
        if lines and lines[0].strip() == "---":
            for line in lines[1:]:
                if line.strip() == "---":
                    break
                if line.startswith("title:"):
                    raw_title = line.split("title:", 1)[1].strip().strip('"').strip("'")
                    if raw_title:
                        return raw_title[:30]
        
        # 2. 检查首个一级标题
        for line in lines:
            line = line.strip()
            if line.startswith("# "):
                raw_title = line[2:].strip()
                if raw_title:
                    return raw_title[:30]
    except Exception:
        pass
    return ""


def cmd_draft(args):
    """将本地 Markdown 填入草稿箱"""
    file_path = Path(args.file).resolve()
    if not file_path.exists():
        print(f"❌ 文章文件不存在: {file_path}")
        return 1

    title = args.title or extract_title_from_md(file_path)
    if not title:
        print("❌ 未能从文章中提取标题，请通过 -t / --title 指定（2-30字）")
        return 1

    pub_args = [
        "--mode", "manual",
        "--content-file", str(file_path),
        "--title", title,
    ]
    # Auto-detect cover image in the same directory if not specified
    cover_path = args.cover
    if not cover_path:
        for ext in ("cover.jpg", "cover.png", "cover.jpeg"):
            candidate = file_path.parent / ext
            if candidate.exists():
                cover_path = str(candidate)
                break
    if cover_path:
        pub_args.extend(["--cover", str(Path(cover_path).resolve())])

    if getattr(args, "wait", None) is not None:
        pub_args.extend(["--wait-seconds", str(args.wait)])
    if getattr(args, "location", None):
        pub_args.extend(["--location", str(args.location)])
    if getattr(args, "exclusive", True) is False:
        pub_args.append("--no-exclusive")
    if getattr(args, "claim", None):
        pub_args.extend(["--claim", str(args.claim)])
    if args.debug:
        pub_args.append("--debug-screenshots")

    print(f"📝 正在自动灌入头条草稿箱: {file_path.name}")
    print(f"📌 解析标题: {title}")
    if cover_path:
        print(f"🖼️ 绑定封面: {Path(cover_path).name}")
    print("💡 模式: manual (灌入草稿箱并保留浏览器供人工确认)")
    return run_script("publisher.py", pub_args)


def cmd_publish(args):
    """全自动发布文章"""
    file_path = Path(args.file).resolve()
    if not file_path.exists():
        print(f"❌ 文章文件不存在: {file_path}")
        return 1

    title = args.title or extract_title_from_md(file_path)
    if not title:
        print("❌ 未能从文章中提取标题，请通过 -t / --title 指定（2-30字）")
        return 1

    pub_args = [
        "--mode", "auto",
        "--content-file", str(file_path),
        "--title", title,
    ]
    # Auto-detect cover image in the same directory if not specified
    cover_path = args.cover
    if not cover_path:
        for ext in ("cover.jpg", "cover.png", "cover.jpeg"):
            candidate = file_path.parent / ext
            if candidate.exists():
                cover_path = str(candidate)
                break
    if cover_path:
        pub_args.extend(["--cover", str(Path(cover_path).resolve())])

    if getattr(args, "location", None):
        pub_args.extend(["--location", str(args.location)])
    if getattr(args, "exclusive", True) is False:
        pub_args.append("--no-exclusive")
    if getattr(args, "claim", None):
        pub_args.extend(["--claim", str(args.claim)])
    if args.headless:
        pub_args.append("--headless")
    if args.debug:
        pub_args.append("--debug-screenshots")

    print(f"🚀 正在全自动发布文章: {file_path.name}")
    print(f"📌 解析标题: {title}")
    if cover_path:
        print(f"🖼️ 绑定封面: {Path(cover_path).name}")
    return run_script("publisher.py", pub_args)


def cmd_scout(args):
    """嗅探头条创作者后台热门灵感与活动"""
    scout_args = ["--limit", str(args.limit)]
    if args.headed:
        scout_args.append("--headed")
    if args.json:
        scout_args.append("--json")
    return run_script("scout_trends.py", scout_args)


def cmd_research(args):
    """根据话题或社会现象进行多视角深度调研并生成方案卡片"""
    res_args = [args.topic]
    if args.json:
        res_args.append("--json")
    return run_script("research_engine.py", res_args)


def cmd_audit(args):
    """审查 Markdown 文章的字数、逻辑闭环与防 AI 痕迹"""
    return run_script("pipeline.py", ["--audit-file", str(Path(args.file).resolve())])


def cmd_radar(args):
    """运行每日热点与选题提案雷达 (自动抓取、过滤并生成3-5套方案)"""
    radar_args = []
    if args.json:
        radar_args.append("--json")
    return run_script("daily_scout.py", radar_args)


def main():
    parser = argparse.ArgumentParser(
        description="今日头条自动化发文系统 (Toutiao Automation Suite)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
常用命令示例:
  python manage.py setup                      # 首次使用：唤起浏览器扫码登录，持久化 Session
  python manage.py status --verify            # 在线验证登录是否仍有效
  python manage.py radar                      # 每日选题雷达：嗅探热点、去重并生成精选方案简报
  python manage.py scout                      # 嗅探头条创作灵感与热门话题 (Top 10)
  python manage.py research "社会现象/话题"    # 深度选题调研并生成3-5套结构化创作方案卡片
  python manage.py audit -f articles/test.md  # 质检审查字数(500-600)、逻辑闭环与去 AI 腔
  python manage.py draft -f articles/test.md  # 自动填入草稿箱，人工在浏览器中预览
  python manage.py publish -f articles/test.md# 全自动正式发布
        """
    )
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # setup
    p_setup = subparsers.add_parser("setup", help="启动专用浏览器完成首次持久化登录")
    p_setup.set_defaults(func=cmd_setup)

    # status
    p_status = subparsers.add_parser("status", help="检查当前账号登录状态")
    p_status.add_argument("--verify", action="store_true", help="在线访问平台验证会话是否失效")
    p_status.set_defaults(func=cmd_status)

    # radar
    p_radar = subparsers.add_parser("radar", help="运行每日热点选题雷达简报 (自动嗅探、去重与生成卡片)")
    p_radar.add_argument("--json", action="store_true", help="以 JSON 格式输出")
    p_radar.set_defaults(func=cmd_radar)

    # scout
    p_scout = subparsers.add_parser("scout", help="嗅探头条创作者后台热门灵感与活动")
    p_scout.add_argument("--limit", type=int, default=10, help="最多展示话题数 (默认10)")
    p_scout.add_argument("--headed", action="store_true", help="显示浏览器窗口")
    p_scout.add_argument("--json", action="store_true", help="以 JSON 格式输出")
    p_scout.set_defaults(func=cmd_scout)

    # research
    p_research = subparsers.add_parser("research", help="输入社会现象或话题，进行多视角深度调研并生成方案")
    p_research.add_argument("topic", help="用户提出的问题、现象或头条热榜话题")
    p_research.add_argument("--json", action="store_true", help="以 JSON 格式输出")
    p_research.set_defaults(func=cmd_research)

    # audit
    p_audit = subparsers.add_parser("audit", help="质检审查文章的字数规范、逻辑闭环与去 AI 腔")
    p_audit.add_argument("-f", "--file", required=True, help="待审查的 Markdown 文章路径")
    p_audit.set_defaults(func=cmd_audit)

    # list
    p_list = subparsers.add_parser("list", help="查看以往历史文章或草稿列表")
    p_list.add_argument("--tab", choices=["published", "draft"], default="published", help="查看分类: published(已发布, 默认) 或 draft(草稿箱)")
    p_list.add_argument("--headed", action="store_true", help="显示浏览器窗口")
    p_list.add_argument("--save", action="store_true", help="保存抓取结果为 outputs/my_articles.json")
    p_list.set_defaults(func=cmd_list)

    # draft
    p_draft = subparsers.add_parser("draft", help="将文章自动灌入头条号草稿箱 (推荐流程)")
    p_draft.add_argument("-f", "--file", required=True, help="Markdown 文章文件路径")
    p_draft.add_argument("-t", "--title", help="文章标题（2-30字，默认解析文章一级标题）")
    p_draft.add_argument("-c", "--cover", help="封面图片路径（可选，默认自动检测同目录下 cover.jpg/png）")
    p_draft.add_argument("-l", "--location", help="发布地/城市标记（如 '广州'，获取同城流量）")
    p_draft.add_argument("--exclusive", action=argparse.BooleanOptionalAction, default=True, help="声明头条首发 (默认开启)")
    p_draft.add_argument("--claim", default="个人观点，仅供参考", help="作品声明 (默认: '个人观点，仅供参考')")
    p_draft.add_argument("--wait", type=int, help="自动保存草稿后等待关闭的秒数（留空则一直保留浏览器直到按 Ctrl+C）")
    p_draft.add_argument("--debug", action="store_true", help="启用调试截图")
    p_draft.set_defaults(func=cmd_draft)

    # publish
    p_pub = subparsers.add_parser("publish", help="全自动发布文章")
    p_pub.add_argument("-f", "--file", required=True, help="Markdown 文章文件路径")
    p_pub.add_argument("-t", "--title", help="文章标题（2-30字，默认解析文章一级标题）")
    p_pub.add_argument("-c", "--cover", help="封面图片路径（可选，默认自动检测同目录下 cover.jpg/png）")
    p_pub.add_argument("-l", "--location", help="发布地/城市标记（如 '广州'，获取同城流量）")
    p_pub.add_argument("--exclusive", action=argparse.BooleanOptionalAction, default=True, help="声明头条首发 (默认开启)")
    p_pub.add_argument("--claim", default="个人观点，仅供参考", help="作品声明 (默认: '个人观点，仅供参考')")
    p_pub.add_argument("--headless", action="store_true", help="无头模式运行（静默后台）")
    p_pub.add_argument("--debug", action="store_true", help="启用调试截图")
    p_pub.set_defaults(func=cmd_publish)

    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(0)

    exit_code = args.func(args)
    sys.exit(exit_code or 0)


if __name__ == "__main__":
    main()
