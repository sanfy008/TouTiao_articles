#!/usr/bin/env python3
"""
Fetch and display past articles from Toutiao Creator Console.
Uses persisted session in browser_state.
"""

import os
import sys
import json
import time
from pathlib import Path

# Fix Windows console UTF-8 encoding
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Ensure temp files stay on D: drive
PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEMP_DIR = PROJECT_ROOT / ".temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("TEMP", str(TEMP_DIR))
os.environ.setdefault("TMP", str(TEMP_DIR))

from patchright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).parent))

from config import BROWSER_PROFILE_DIR, STATE_FILE
from browser_utils import BrowserFactory

ARTICLES_URL = "https://mp.toutiao.com/profile_v4/graphic/articles"


def fetch_articles(headless: bool = True, max_scroll: int = 3, tab: str = "published"):
    """
    Open articles management page and extract recent article metadata.
    tab can be 'published' (default) or 'draft' / '草稿箱'.
    """
    if not STATE_FILE.exists() and not BROWSER_PROFILE_DIR.exists():
        print("❌ 未检测到登录凭证，请先运行: python manage.py setup")
        return []

    is_draft_tab = tab in ("draft", "草稿", "草稿箱")
    target_name = "草稿箱" if is_draft_tab else "历史文章"
    print(f"🔍 正在拉取头条号{target_name}列表...")
    articles = []

    with sync_playwright() as playwright:
        try:
            context = BrowserFactory.launch_persistent_context(
                playwright,
                headless=headless,
                user_data_dir=str(BROWSER_PROFILE_DIR),
                state_file=str(STATE_FILE),
            )
            page = context.new_page()
            page.goto(ARTICLES_URL, wait_until="domcontentloaded", timeout=45000)
            time.sleep(3)

            # 检查是否被重定向到登录页
            if "auth/page/login" in page.url or "sso.toutiao.com" in page.url:
                print("⚠️ 登录会话已过期，请重新登录: python manage.py setup")
                context.close()
                return []

            if is_draft_tab:
                draft_btn = page.locator("text=草稿箱").first
                if draft_btn.is_visible():
                    draft_btn.click()
                    time.sleep(2)

            # 滚动加载更多
            for _ in range(max_scroll):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(1.5)

            # 提取文章列表 DOM
            if is_draft_tab:
                extracted = page.evaluate("""() => {
                    const results = [];
                    const cards = document.querySelectorAll('.draft-page .list > div, .draft-page [class*="item"], .draft-page .list, tr, [class*="card"]');
                    cards.forEach(card => {
                        const text = card.innerText || '';
                        if (!text.includes('编辑') && !text.includes('删除')) return;
                        const lines = text.split('\\n').map(l => l.trim()).filter(l => l.length > 0);
                        for (const line of lines) {
                            if (line.length > 2 && !['云端', '本地', '体裁：', '全部', '~', '编辑', '删除'].includes(line) && !line.includes('共') && !line.includes('条内容') && !line.includes('分钟前') && !line.includes('小时前') && !line.includes('天前')) {
                                results.push({
                                    title: line,
                                    status: '草稿',
                                    summary: text.replace(/\\s+/g, ' ').slice(0, 160)
                                });
                                break;
                            }
                        }
                    });
                    return results;
                }""")
            else:
                extracted = page.evaluate("""() => {
                    const results = [];
                    const items = document.querySelectorAll('.byte-table-row, .article-card, tr, .article-item, [class*="article-card"]');
                    items.forEach(el => {
                        const text = el.innerText || '';
                        if (!text.trim()) return;
                        
                        const titleEl = el.querySelector('a, .title, [class*="title"]') || el;
                        const title = (titleEl ? titleEl.innerText : '').split('\\n')[0].trim();
                        
                        let status = '已发布';
                        if (text.includes('草稿')) status = '草稿';
                        else if (text.includes('审核中')) status = '审核中';
                        else if (text.includes('未通过')) status = '未通过';

                        if (title && title.length > 2 && !title.includes('操作') && !title.includes('状态') && !title.includes('标题')) {
                            results.push({
                                title: title,
                                status: status,
                                summary: text.replace(/\\s+/g, ' ').slice(0, 160)
                            });
                        }
                    });
                    return results;
                }""")

            # 去重
            seen = set()
            for item in extracted:
                t = item.get("title")
                if t and t not in seen:
                    seen.add(t)
                    articles.append(item)

            context.close()
        except Exception as e:
            print(f"❌ 读取文章列表失败: {e}")

    return articles


def main():
    import argparse
    parser = argparse.ArgumentParser(description="查看头条号历史文章或草稿")
    parser.add_argument("--tab", choices=["published", "draft"], default="published", help="查看的分类: published(已发布) 或 draft(草稿箱)")
    parser.add_argument("--headed", action="store_true", help="显示浏览器窗口")
    parser.add_argument("--save", action="store_true", help="保存文章列表为 JSON 文件")
    args = parser.parse_args()

    articles = fetch_articles(headless=not args.headed, tab=args.tab)
    if not articles:
        print("未获取到文章列表（可能暂无文章或需要登录）。")
        return

    print(f"\n📑 成功检索到 {len(articles)} 篇近期文章：\n")
    print(f"{'序号':<4} | {'状态':<6} | {'文章标题'}")
    print("-" * 60)
    for idx, art in enumerate(articles, 1):
        print(f"{idx:<4} | {art['status']:<6} | {art['title']}")

    if args.save:
        out_path = Path("outputs") / "my_articles.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
        print(f"\n💾 详细文章数据已保存至: {out_path}")


if __name__ == "__main__":
    main()
