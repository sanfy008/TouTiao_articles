#!/usr/bin/env python3
"""
Toutiao Inspiration & Hotspot Scout (创作灵感与热点嗅探引擎)
Scrapes trending topics and creator incentives from Toutiao Creator Console.
"""

import os
import sys
import json
import re
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# Fix Windows console UTF-8 encoding
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from config import DATA_DIR, BROWSER_PROFILE_DIR, STATE_FILE, BROWSER_ARGS
from browser_utils import BrowserFactory

HOTSPOT_URL = "https://mp.toutiao.com/profile_v4/activity/hot-spot"
TASKLIST_URL = "https://mp.toutiao.com/profile_v4/activity/task-list"


def parse_metric_to_number(metric_str: str) -> float:
    """Parse '101.6万', '1.2亿', '3,500' to standard integer/float value"""
    if not metric_str:
        return 0.0
    cleaned = metric_str.replace(",", "").strip()
    try:
        if "亿" in cleaned:
            num = float(cleaned.replace("亿", "").strip())
            return num * 100000000
        elif "万" in cleaned:
            num = float(cleaned.replace("万", "").strip())
            return num * 10000
        else:
            # Match first floating/int number
            m = re.search(r"[\d.]+", cleaned)
            return float(m.group(0)) if m else 0.0
    except Exception:
        return 0.0


def extract_hotspots_from_page(page) -> List[Dict[str, Any]]:
    """Extract hot spot topic cards from the hot-spot page DOM"""
    raw_cards = page.evaluate("""() => {
        const results = [];
        const items = document.querySelectorAll('.hot-item-title, [class*="hot-item-title"]');
        items.forEach(el => {
            const tag = (el.innerText || '').trim();
            if (!tag) return;
            
            // Find parent container
            let p = el.parentElement;
            for (let i = 0; i < 4 && p; i++) {
                if (p.innerText && (p.innerText.includes('阅读') || p.innerText.includes('讨论'))) {
                    break;
                }
                if (p.parentElement) p = p.parentElement;
            }
            const fullText = p ? p.innerText : '';
            results.push({
                tag: tag,
                full_text: fullText
            });
        });
        return results;
    }""")

    hotspots = []
    seen = set()

    for item in raw_cards:
        tag = item.get("tag", "").strip()
        if not tag or tag in seen:
            continue
        seen.add(tag)

        full_text = item.get("full_text", "")
        # Extract reads and discussions
        # Pattern: 阅读 101.6万 / 讨论 894
        reads_match = re.search(r"阅读\s*([\d.,万亿]+)", full_text)
        discussions_match = re.search(r"讨论\s*([\d.,万亿]+)", full_text)

        reads_str = reads_match.group(1) if reads_match else "0"
        discussions_str = discussions_match.group(1) if discussions_match else "0"

        reads_num = parse_metric_to_number(reads_str)
        disc_num = parse_metric_to_number(discussions_str)

        # Calculate a combined heat score
        heat_score = reads_num + disc_num * 50

        # Extract incentive if mentioned (e.g. 瓜分万元奖金)
        incentive = ""
        inc_match = re.search(r"(瓜分[\d万]+奖金|赢[\d万]+流量|奖励[\d万]+)", full_text)
        if inc_match:
            incentive = inc_match.group(1)

        hotspots.append({
            "tag": tag,
            "reads": reads_str,
            "discussions": discussions_str,
            "reads_num": reads_num,
            "discussions_num": disc_num,
            "heat_score": heat_score,
            "incentive": incentive,
            "category": "推荐灵感",
        })

    # Sort descending by heat score
    hotspots.sort(key=lambda x: x["heat_score"], reverse=True)
    return hotspots


def extract_tasks_from_page(page) -> List[Dict[str, Any]]:
    """Extract official incentive campaigns from task-list page"""
    raw_tasks = page.evaluate("""() => {
        const results = [];
        const taskCards = document.querySelectorAll('.task-card, [class*="task-card"], .task-item, [class*="task-item"]');
        taskCards.forEach(el => {
            const text = el.innerText || '';
            if (text.trim().length > 10) {
                results.push(text);
            }
        });
        return results;
    }""")

    tasks = []
    for text in raw_tasks:
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        if lines:
            tasks.append({
                "title": lines[0],
                "details": " | ".join(lines[1:4]),
                "raw_text": text
            })
    return tasks


def scout_trends(headless: bool = True, limit: int = 10) -> Dict[str, Any]:
    """
    Scout trending topics and tasks from Toutiao.
    Returns dictionary with 'hotspots' and 'tasks'.
    """
    if not STATE_FILE.exists() and not BROWSER_PROFILE_DIR.exists():
        print("⚠️ 未检测到登录凭证，请先运行: python manage.py setup 进行持久化登录。")
        return {"hotspots": [], "tasks": []}

    print("🔎 正在连接今日头条创作者后台嗅探创作灵感与热门话题...")

    from patchright.sync_api import sync_playwright

    hotspots = []
    tasks = []

    with sync_playwright() as playwright:
        try:
            context = BrowserFactory.launch_persistent_context(
                playwright,
                headless=headless,
                user_data_dir=str(BROWSER_PROFILE_DIR),
                state_file=str(STATE_FILE),
            )
            page = context.new_page()

            # 1. Scrape Hot-spot
            page.goto(HOTSPOT_URL, wait_until="domcontentloaded", timeout=45000)
            time.sleep(3)

            # Check if redirected to login
            if "auth/page/login" in page.url or "sso.toutiao.com" in page.url:
                print("⚠️ 登录会话已过期，请重新登录: python manage.py setup")
                context.close()
                return {"hotspots": [], "tasks": []}

            hotspots = extract_hotspots_from_page(page)

            # 2. Scrape Task-list
            page.goto(TASKLIST_URL, wait_until="domcontentloaded", timeout=45000)
            time.sleep(2)
            tasks = extract_tasks_from_page(page)

            context.close()
        except Exception as e:
            print(f"❌ 嗅探热点时发生异常: {e}")

    # Output directory
    out_dir = PROJECT_ROOT / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    res_path = out_dir / "scout_trends.json"

    result_data = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_hotspots": len(hotspots),
        "hotspots": hotspots[:limit],
        "tasks": tasks,
    }

    with open(res_path, "w", encoding="utf-8") as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)

    return result_data


def format_heat(num: float) -> str:
    """Format heat number to readable human Chinese string"""
    if num >= 100000000:
        return f"{num / 100000000:.1f}亿"
    elif num >= 10000:
        return f"{num / 10000:.1f}万"
    else:
        return str(int(num))


def display_scout_report(scout_data: Dict[str, Any]):
    """Pretty print scouted trends into terminal cards"""
    hotspots = scout_data.get("hotspots", [])
    tasks = scout_data.get("tasks", [])

    print("\n" + "=" * 70)
    print("🔥 今日头条创作灵感与热门选题雷达 (Toutiao Topic Radar)")
    print("=" * 70)

    if not hotspots:
        print("暂无抓取到热门话题，请确认网络连接或登录状态。")
        return

    print(f"\n📊 捕获精选推荐话题 (Top {len(hotspots)}):")
    print(f"{'排名':<4} | {'阅读量':<8} | {'讨论量':<8} | {'话题名称与激励'}")
    print("-" * 70)

    for i, item in enumerate(hotspots, 1):
        tag = item["tag"]
        reads = item["reads"]
        discs = item["discussions"]
        incentive = f" 🎁 [{item['incentive']}]" if item.get("incentive") else ""
        print(f"{i:<4} | {reads:<8} | {discs:<8} | {tag}{incentive}")

    if tasks:
        print(f"\n🎁 正在进行的平台创作活动 ({len(tasks)}项):")
        for t in tasks:
            print(f"  • {t['title']}: {t.get('details', '')}")

    print("\n💡 提示：使用 `python manage.py research \"<话题或社会现象>\"` 可自动展开深度调研并生成3-5套结构化创作方案。")
    print("=" * 70 + "\n")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="今日头条热门话题与创作灵感嗅探")
    parser.add_argument("--limit", type=int, default=10, help="最多抓取的话题数量 (默认10)")
    parser.add_argument("--headed", action="store_true", help="显示浏览器窗口")
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出结果")
    args = parser.parse_args()

    data = scout_trends(headless=not args.headed, limit=args.limit)
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        display_scout_report(data)


if __name__ == "__main__":
    main()
