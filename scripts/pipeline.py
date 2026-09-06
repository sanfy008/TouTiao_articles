#!/usr/bin/env python3
"""
Toutiao End-to-End Publishing Pipeline (头条全链路协同发布流水线)
Orchestrates:
1. Inspiration Scouting & Deep Research
2. Subagent 1: Drafting (500-600 words, grounded, colloquial)
3. Subagent 2: Quality & Anti-AI Critique (Assertion of logic, words, blacklists)
4. Subagent 3: Visual Direction (16:9 cinematic cover generation)
5. Subagent 4: Typesetting & Automation (Markdown normalization & Playwright publishing)
"""

import sys
import re
import time
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

# Fix Windows console UTF-8 encoding
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from research_engine import ResearchEngine


class ContentAuditor:
    """
    Subagent: Quality & Anti-AI Critique Auditor.
    Performs deterministic assertions on word count, logic consistency,
    platitude blacklists, and hashtag normalization.
    """

    MIN_WORDS = 480
    MAX_WORDS = 620
    MAX_PARAGRAPH_CHARS = 110

    @classmethod
    def audit(cls, title: str, content: str) -> Tuple[bool, List[str], Dict[str, Any]]:
        issues = []
        
        # 1. Count Chinese characters & words
        # Strip frontmatter and tags
        body = content
        if body.startswith("---"):
            parts = body.split("---", 2)
            if len(parts) >= 3:
                body = parts[2]
        
        # Remove tags at tail
        body_no_tags = re.sub(r"#.*?#", "", body)
        # Count Chinese chars
        chinese_chars = re.findall(r"[\u4e00-\u9fa5]", body_no_tags)
        char_count = len(chinese_chars)

        if char_count < cls.MIN_WORDS:
            issues.append(f"字数过少（纯汉字 {char_count} 字，最低要求 {cls.MIN_WORDS} 字）")
        elif char_count > cls.MAX_WORDS:
            issues.append(f"字数超标（纯汉字 {char_count} 字，最高限制 {cls.MAX_WORDS} 字）")

        # 2. Platitude blacklist check
        for plat in ResearchEngine.PLATITUDE_BLACKLIST:
            if plat in body:
                issues.append(f"包含悬浮 AI 套话: '{plat}'")

        # 3. Logic consistency check
        # Check if title promises a specific number
        num_patterns = [
            (r"三个字", 3),
            (r"四个字", 4),
            (r"六个字", 6),
            (r"八个字", 8),
            (r"九个字", 9),
            (r"两笔账", 2),
            (r"三笔账", 3),
            (r"三句话", 3),
        ]
        for pattern, expected_count in num_patterns:
            if re.search(pattern, title):
                # Search for explicit patterns like 这九个字：xxx or quotes
                found_exact = False
                
                # Check for "这X个字[：:]([^。\n]+)"
                colon_match = re.search(r"这[一二三四五六七八九十]+个字[：:]([^。\n]+)", body)
                if colon_match:
                    chars = re.findall(r"[\u4e00-\u9fa5]", colon_match.group(1))
                    if len(chars) == expected_count:
                        found_exact = True

                # Also check quotes like “xxx” or ‘xxx’
                if not found_exact:
                    quote_matches = re.findall(r"[“‘]([^”’\n]+)[”’]", body)
                    for q in quote_matches:
                        chars = re.findall(r"[\u4e00-\u9fa5]", q)
                        if len(chars) == expected_count:
                            found_exact = True
                            break

                if not found_exact:
                    issues.append(f"逻辑一致性警告：标题承诺‘{pattern}’，正文中未检测到严格对应的 {expected_count} 字结论")

        # 4. Hashtag format check
        if "## 话题" in content or "##话题" in content:
            issues.append("文末包含 Markdown 标题级的 '## 话题'，必须改为纯净段落标签")
        if "话题：" in content or "话题:" in content:
            issues.append("文末包含冗余的 '话题：' 前缀，必须剔除")

        # 5. Astra Prose Check: Reject Bullet Points
        for line in body.splitlines():
            line_str = line.strip()
            if not line_str.startswith("#") and not line_str.startswith("![") and not line_str.startswith("---"):
                if re.match(r"^[-*•]\s+", line_str) or re.match(r"^\d+[\.、]\s+", line_str):
                    issues.append("包含列表项目符号 (bullet points)，违反 GPT-6 Astra 纯散文自然叙述规范，请改用自然段落")
                    break

        # 6. Astra Mobile Rhythm: Short Paragraph Check (50-80 target, max 110)
        paragraphs = [p.strip() for p in body_no_tags.splitlines() if p.strip() and not p.strip().startswith("![") and not p.strip().startswith("---")]
        if len(paragraphs) > 1:
            long_paras = []
            for idx, p in enumerate(paragraphs, 1):
                p_chars = len(re.findall(r"[\u4e00-\u9fa5]", p))
                if p_chars > cls.MAX_PARAGRAPH_CHARS:
                    long_paras.append((idx, p_chars))
            if long_paras:
                issues.append(
                    f"存在段落过长（第 {[lp[0] for lp in long_paras]} 段纯汉字最高达 {max(lp[1] for lp in long_paras)} 字），不利于手机端阅读（建议单段控制在 50-80 字，上限 {cls.MAX_PARAGRAPH_CHARS} 字）"
                )

        # 7. Astra Anti-Slop: Overuse of mechanical contrastive framing ('不是...而是...', '不仅...更是...')
        contrastive_matches = re.findall(
            r"(?:不是[^。！？\n]{1,25}[，, ]*而是|不仅[^。！？\n]{1,25}[，, ]*更是|表面上[^。！？\n]{1,25}[，, ]*实际上)",
            body,
        )
        if len(contrastive_matches) > 2:
            issues.append(f"包含过多机械对仗 AI 腔（检测到 {len(contrastive_matches)} 处‘不是...而是/不仅...更是’，建议改用直接动词陈述）")

        metrics = {
            "char_count": char_count,
            "title_length": len(title),
            "paragraph_count": len(paragraphs),
            "passed": len(issues) == 0
        }
        return len(issues) == 0, issues, metrics


def prepare_article_directory(
    title: str,
    content: str,
    cover_source: Optional[str] = None,
    base_dir: Optional[Path] = None,
) -> Path:
    """
    Sets up the standardized directory structure:
    articles/MM/DD/Title/
    - article.md
    - cover.jpg
    """
    now = time.localtime()
    month_dir = f"{now.tm_mon:02d}"
    day_dir = f"{now.tm_mday:02d}"

    # Clean title for directory name (remove special characters)
    clean_dir_name = re.sub(r'[\\/:*?"<>|#\s]', '_', title)[:30].strip('_')
    root = base_dir if base_dir is not None else (PROJECT_ROOT / "articles")
    target_dir = root / month_dir / day_dir / clean_dir_name
    target_dir.mkdir(parents=True, exist_ok=True)

    article_path = target_dir / "article.md"
    article_path.write_text(content, encoding="utf-8")

    if cover_source and Path(cover_source).exists():
        target_cover = target_dir / "cover.jpg"
        shutil.copy2(cover_source, target_cover)

    return target_dir


def main():
    import argparse
    parser = argparse.ArgumentParser(description="今日头条全链路发布管线 (Toutiao Content Pipeline)")
    parser.add_argument("--topic", help="选题或社会现象")
    parser.add_argument("--scout", action="store_true", help="先自动从头条灵感嗅探热榜")
    parser.add_argument("--audit-file", help="对指定 Markdown 文件执行质检审核")
    args = parser.parse_args()

    if args.audit_file:
        path = Path(args.audit_file).resolve()
        if not path.exists():
            print(f"❌ 文件不存在: {path}")
            sys.exit(1)
        content = path.read_text(encoding="utf-8")
        title = path.name
        # Try extract title
        for line in content.splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                break
        passed, issues, metrics = ContentAuditor.audit(title, content)
        print("\n" + "=" * 60)
        print(f"🧐 文章质检报告: {title}")
        print(f"📊 纯中文字数: {metrics['char_count']} 字 (标准区间: 480-620字)")
        print(f"🎯 标题字数: {metrics['title_length']} 字")
        if passed:
            print("✅ 质检全项通过！无 AI 腔套话，逻辑结构闭环，符合头条爆款规范。")
        else:
            print("⚠️ 发现以下待修正项:")
            for issue in issues:
                print(f"  • {issue}")
        print("=" * 60 + "\n")
        sys.exit(0 if passed else 1)

    print("🚀 Toutiao Content Pipeline Ready.")


if __name__ == "__main__":
    main()
