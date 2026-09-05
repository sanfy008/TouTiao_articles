#!/usr/bin/env python3
"""
Daily Toutiao Scout & Proposal Radar (每日头条热点嗅探与选题提案雷达)
Automatically scouts trends, filters out already published topics,
runs deep research on the top candidates, and compiles 3-5 structured proposals.
"""

import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List

# Fix Windows console UTF-8 encoding
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from scout_trends import scout_trends
from research_engine import ResearchEngine


def get_published_titles() -> List[str]:
    """Retrieve titles of articles already in articles/ directory to avoid duplicates"""
    titles = []
    articles_dir = PROJECT_ROOT / "articles"
    if articles_dir.exists():
        for md_file in articles_dir.rglob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                for line in content.splitlines():
                    if line.startswith("title:"):
                        titles.append(line.split("title:", 1)[1].strip().strip('"\''))
                        break
                    elif line.startswith("# "):
                        titles.append(line[2:].strip())
                        break
            except Exception:
                pass
    return titles


def generate_daily_radar(limit_scout: int = 10, top_proposals: int = 4) -> Dict[str, Any]:
    """
    Run full daily scout & research radar.
    Returns structured radar report.
    """
    print("🌅 正在启动今日头条每日热点雷达 (Daily Topic Radar)...")
    scout_data = scout_trends(headless=True, limit=limit_scout)
    hotspots = scout_data.get("hotspots", [])
    tasks = scout_data.get("tasks", [])

    published = get_published_titles()
    published_str = " ".join(published)

    # Filter out already covered topics and non-essay prompts (like couplets)
    filtered_hotspots = []
    for h in hotspots:
        tag_clean = h["tag"].strip("#")
        # Filter couplet/interactive micro-posts
        if any(w in tag_clean for w in ["上联", "下联", "对联", "求对", "接龙"]):
            continue
        # Check if significantly overlaps with past titles
        if any(w in published_str for w in tag_clean.split("，") if len(w) > 3):
            continue
        filtered_hotspots.append(h)

    candidates = filtered_hotspots[:top_proposals]
    if not candidates:
        candidates = hotspots[:top_proposals]

    proposals_pool = []
    for cand in candidates:
        topic_text = cand["tag"]
        engine = ResearchEngine(topic_text)
        research_res = engine.run_full_research()
        props = research_res.get("proposals", [])
        if props:
            # Pick the most resonant proposal from each candidate
            best_prop = props[0]
            best_prop["source_tag"] = topic_text
            best_prop["reads"] = cand.get("reads", "0")
            best_prop["discussions"] = cand.get("discussions", "0")
            best_prop["incentive"] = cand.get("incentive", "")
            proposals_pool.append(best_prop)

    now_str = time.strftime("%Y-%m-%d_%H%M")
    out_dir = PROJECT_ROOT / "output" / "daily_suggestions"
    out_dir.mkdir(parents=True, exist_ok=True)

    report_data = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_scouted": len(hotspots),
        "active_tasks": tasks,
        "selected_proposals": proposals_pool
    }

    json_path = out_dir / f"radar_{now_str}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)

    # Also format markdown
    md_path = out_dir / f"radar_{now_str}.md"
    _write_radar_markdown(report_data, md_path)

    return report_data


def _write_radar_markdown(data: Dict[str, Any], path: Path):
    lines = []
    lines.append(f"# 今日头条每日选题推荐雷达 ({data['timestamp']})\n")
    if data.get("active_tasks"):
        lines.append("## 🎁 平台创作激励活动")
        for t in data["active_tasks"]:
            lines.append(f"- **{t['title']}**：{t.get('details', '')}")
        lines.append("")

    lines.append("## 🎯 精选推荐创作方案")
    for i, p in enumerate(data.get("selected_proposals", []), 1):
        lines.append(f"### 方案 {i}：{p['title']}")
        lines.append(f"- **来源话题**：{p['source_tag']} (阅读: {p['reads']} | 讨论: {p['discussions']})")
        lines.append(f"- **定位风格**：{p['angle_type']} | 字数建议: {p['target_words']}")
        lines.append(f"- **黄金导语**：{p['hook']}")
        lines.append(f"- **核心对立**：{p['conflict']}")
        lines.append(f"- **16:9 配图构想**：`{p['visual_prompt']}`")
        lines.append(f"- **话题标签**：{' '.join(p['tags'])}\n")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def display_daily_radar(data: Dict[str, Any]):
    print("\n" + "=" * 76)
    print(f"📢 今日头条每日选题推荐简报 ({data['timestamp']})")
    print("=" * 76)

    proposals = data.get("selected_proposals", [])
    if not proposals:
        print("今日暂无抓取到推荐选题。")
        return

    for i, p in enumerate(proposals, 1):
        inc = f" 🎁[{p['incentive']}]" if p.get("incentive") else ""
        print(f"\n【推荐方案 {i}】{p['title']}")
        print(f"  🔥 话题热度：{p['source_tag']}（阅读 {p['reads']} / 讨论 {p['discussions']}{inc}）")
        print(f"  📌 风格定位：{p['angle_type']} | 建议篇幅：{p['target_words']}")
        print(f"  ⚡ 抓人引子：\"{p['hook']}\"")
        print(f"  ⚖️ 核心矛盾：{p['conflict']}")
        print(f"  🏷️ 标签规划：{' '.join(p['tags'])}")
        print("  " + "-" * 72)

    print("\n💡 用户指令支持：")
    print("  👉 在对话框中直接回复：\"确认执行方案 1\" 或 \"选方案 2\"")
    print("  👉 Agent 将自动指派 Subagents 协同完成：撰写 ➔ 质检 ➔ 16:9 配图 ➔ 排版 ➔ 正式发布。")
    print("=" * 76 + "\n")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="头条每日热点雷达")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出")
    args = parser.parse_args()

    data = generate_daily_radar()
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        display_daily_radar(data)


if __name__ == "__main__":
    main()
