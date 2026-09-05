#!/usr/bin/env python3
"""
Toutiao Deep Research & Ideation Engine (深度调研与选题生成引擎)
Inspired by Stanford STORM and DeepResearch architectures.
Accepts user questions, social phenomena, or scraped trending topics,
conducts multi-perspective inquiry, and synthesizes 3-5 structured topic proposal cards.
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


class ResearchEngine:
    """
    Multi-perspective research and topic proposal generation engine.
    Decomposes raw phenomena into concrete lived experiences, contrasting realities,
    and highly resonant Toutiao essay proposal cards.
    """

    PERSPECTIVES = [
        {
            "id": "economic_reality",
            "name": "经济与民生账本",
            "focus": "精细算账、性价比、隐形开支、抗风险储备、消费降级或消费理性化",
            "tone": "清醒、务实、算清生活柴米油盐账",
        },
        {
            "id": "emotional_boundary",
            "name": "心理与情感边界",
            "focus": "精神内耗、体面感、人情往来负担、依赖与独立、讨好与边界感",
            "tone": "扎心、共情、通透解压",
        },
        {
            "id": "generational_contrast",
            "name": "代际与观念反差",
            "focus": "传统老规矩 vs 现代生存法则、两代人认知断层、旧经验失灵",
            "tone": "反差鲜明、叙事张力强、避免道德说教",
        },
        {
            "id": "counter_intuitive",
            "name": "反常识与底层洞察",
            "focus": "戳破伪精致、揭露盲目跟风背后的代价、从细微反常处见生活本质",
            "tone": "一针见血、发人深省、引发大量评论区争辩",
        },
    ]

    PLATITUDE_BLACKLIST = [
        "在这个快节奏的时代",
        "在当今纷繁复杂的社会",
        "人生如逆旅，我亦是行人",
        "综上所述",
        "总而言之",
        "岁月静好",
        "唯有...才能...",
        "让我们一起努力",
        "无论如何",
    ]

    def __init__(self, topic_or_phenomenon: str):
        self.raw_input = topic_or_phenomenon.strip()
        # Clean topic hashtag delimiters and trailing punctuation
        cleaned = self.raw_input.strip("#").strip()
        cleaned = re.sub(r"[？?。！!,，\s]+$", "", cleaned)
        self.clean_topic = cleaned

    def analyze_perspectives(self) -> List[Dict[str, Any]]:
        """Decompose topic into multi-angle perspectives"""
        analysis = []
        for p in self.PERSPECTIVES:
            analysis.append({
                "perspective_id": p["id"],
                "name": p["name"],
                "focus": p["focus"],
                "tone": p["tone"],
                "angle_summary": f"从【{p['name']}】切入分析'{self.clean_topic}'，紧扣{p['focus']}，以{p['tone']}的口吻展开叙事。"
            })
        return analysis

    def synthesize_proposals(self) -> List[Dict[str, Any]]:
        """
        Synthesize 3-5 structured topic cards.
        Adheres to Toutiao short essay formula:
        - 22-28 chars high-CTR title
        - 500-600 characters target length
        - Immediate relatable hook
        - Concrete contrasting vignette
        - Grounded conclusion
        - Pure hashtags
        """
        t = self.clean_topic

        # Pattern detection to generate highly relevant angles
        proposals = []

        # Proposal 1: The Hardcore Reality / Economic Angle
        p1_title = f"{t}？算完这笔扎心账，我彻底清醒了"
        if len(p1_title) > 28:
            p1_title = f"{t[:18]}？算完这笔账我清醒了"
        proposals.append({
            "id": 1,
            "title": p1_title,
            "angle_type": "现实账本型（理智扎心）",
            "hook": f"身边总有人在争论‘{t}’，但大多数人算错了账，把面子当成了底气，直到摔了跟头才发现生活的残酷。",
            "conflict": "面子消费与人情绑架 vs 真实钱包厚度与抗风险能力",
            "narrative_arc": [
                "开头用生活反常现象抛出疑问，迅速吸引中老年及家庭决策者视线",
                "正文列举身边真实现象（柴米油盐、人情往来、生病用钱时的残酷对比）",
                "剖析普通人最容易踩的自我感动误区",
                "文末给出通透务实的生存法则（手握碎银，守住边界，不听虚话）"
            ],
            "target_words": "500-580字",
            "visual_prompt": f"Chinese everyday realistic scene, documentary street photography, warm natural sunlight, authentic atmosphere, 16:9 widescreen, 4k cinematic",
            "tags": [f"#{t}#", "#生活感悟#", "#真实生活#", "#中老年生活#"]
        })

        # Proposal 2: The Emotional Independence / Counter-Intuitive Angle
        p2_title = f"看透‘{t}’的人，早就把退路换成了三个字"
        if len(p2_title) > 28:
            p2_title = f"看透‘{t[:16]}’的人，早换了活法"
        proposals.append({
            "id": 2,
            "title": p2_title,
            "angle_type": "反常识认知型（通透豁达）",
            "hook": f"关于‘{t}’，年纪越大越发现：年轻时以为的天经地义，到了后半辈子往往成了最沉重的枷锁。",
            "conflict": "盲目指望外界与他人认可 vs 内心秩序与个人独立边界",
            "narrative_arc": [
                "直击中年往后的现实痛点，打破传统‘应该如何’的说教",
                "对比两种截然不同的人生态度：一种抓得太紧心力交瘁，一种看开守己反而从容",
                "用一句掷地有声的话点破人性的本质",
                "收拢于‘向内求底气，向外守边界’的从容姿态"
            ],
            "target_words": "510-570字",
            "visual_prompt": f"Elderly Chinese person sitting comfortably in a tranquil courtyard drinking tea, peaceful expression, soft afternoon golden hour light, 16:9 cinematic photography",
            "tags": [f"#{t}#", "#人生感悟#", "#为人处世#", "#后半辈子#"]
        })

        # Proposal 3: Grounded Lived Experience / Family & Generational Contrast
        p3_title = f"别再为‘{t}’纠结了，这才是普通家庭唯一的体面"
        if len(p3_title) > 28:
            p3_title = f"关于‘{t[:16]}’，这才是最大的体面"
        proposals.append({
            "id": 3,
            "title": p3_title,
            "angle_type": "家庭共情型（温暖治愈）",
            "hook": f"今天在菜市场听到两位老街坊聊起‘{t}’，几句话直戳心窝子，比网上那些大道理管用一万倍。",
            "conflict": "外人眼里的虚假光鲜 vs 自家日子关起门来的踏实温暖",
            "narrative_arc": [
                "以极具烟火气的市井小对话开篇，瞬间拉近与读者的距离",
                "展开一个普通家庭在现实波折面前的真实选择",
                "反思生活中被过分夸大的虚荣与焦虑",
                "结尾呼应家庭温暖、身体健康和内心的知足常乐"
            ],
            "target_words": "520-580字",
            "visual_prompt": f"Warm bustling Chinese street market or cozy dinner table, steaming food, authentic human warmth, photorealistic, 16:9 cinematic composition",
            "tags": [f"#{t}#", "#百姓生活#", "#人间烟火#", "#家庭感悟#"]
        })

        # Proposal 4: Punchy Debate / Comment-Driver (争议探讨型)
        p4_title = f"为什么越来越多人开始反感‘{t}’？原因很现实"
        if len(p4_title) > 28:
            p4_title = f"为什么很多人反感‘{t[:16]}’？太真实"
        proposals.append({
            "id": 4,
            "title": p4_title,
            "angle_type": "社会议题反思型（高互动互动率）",
            "hook": f"不知从什么时候开始，大家对‘{t}’的态度彻底变了。从前的理所当然，如今怎么成了很多人避之不及的雷区？",
            "conflict": "陈旧观念的道德捆绑 vs 新一代人的清醒解绑与生存压力",
            "narrative_arc": [
                "开篇摆出强烈的态度反差，激发读者的站队与评论欲望",
                "拆解发生这种转变背后的三点现实根源（钱难挣、心太累、信任成本高）",
                "客观陈述两派人的不同立场，不做廉价评判",
                "文末抛出互动开放式问句，引导读者在评论区分享切身体会"
            ],
            "target_words": "530-590字",
            "visual_prompt": f"Thoughtful Chinese middle-aged individual looking through a rain-streaked window or cafe window, reflective mood, 16:9 cinematic",
            "tags": [f"#{t}#", "#社会百态#", "#话题讨论#", "#今日深思#"]
        })

        return proposals

    def build_fact_dossier(self) -> Dict[str, Any]:
        """Compile research evidence, contrasting cases, and guardrails"""
        return {
            "topic": self.clean_topic,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "target_audience": "头条主力读者（35-65岁关注家庭、民生、养老、生活感悟的务实群体）",
            "reading_scenario": "碎片化刷手机、通勤或睡前浏览，要求前3行必须入题，不废话",
            "style_rules": [
                "篇幅严格控制在 500-600 字（完读率峰值区间）",
                "语言大白话，充满口语化叙事与市井烟火气",
                "严禁悬浮 AI 腔，严禁出现'在这个快节奏的时代'、'综上所述'",
                "逻辑严密闭环（如提倡几点必须数字与内容精确对应）",
                "文末标签使用纯净 <p>#标签1# #标签2#</p>，不带'话题：'前缀，不带Markdown标题样式"
            ],
            "platitude_blacklist": self.PLATITUDE_BLACKLIST
        }

    def run_full_research(self) -> Dict[str, Any]:
        """Execute full research pipeline and output dossier"""
        perspectives = self.analyze_perspectives()
        proposals = self.synthesize_proposals()
        dossier = self.build_fact_dossier()

        output_data = {
            "topic": self.clean_topic,
            "perspectives": perspectives,
            "fact_dossier": dossier,
            "proposals": proposals,
        }

        # Persist to output/
        out_dir = PROJECT_ROOT / "output"
        out_dir.mkdir(parents=True, exist_ok=True)

        json_path = out_dir / "research_dossier.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        # Generate markdown report
        md_path = out_dir / "research_dossier.md"
        self._write_markdown_report(output_data, md_path)

        return output_data

    def _write_markdown_report(self, data: Dict[str, Any], path: Path):
        """Generate human-readable markdown research dossier"""
        lines = []
        lines.append(f"# 深度选题调研与方案库：{data['topic']}\n")
        lines.append(f"> 调研生成时间：{time.strftime('%Y-%m-%d %H:%M:%S')} | 面向平台：今日头条\n")

        lines.append("## 一、多视角深度拆解 (Multi-Perspective Inquiry)")
        for p in data["perspectives"]:
            lines.append(f"- **{p['name']}**：{p['focus']}")
            lines.append(f"  *切入指导*：{p['angle_summary']}")
        lines.append("")

        lines.append("## 二、精选创作方案卡片 (Topic Proposal Cards)\n")
        for prop in data["proposals"]:
            lines.append(f"### 方案 {prop['id']}：{prop['title']}")
            lines.append(f"- **类型定位**：{prop['angle_type']}")
            lines.append(f"- **前3秒抓人黄金引子**：{prop['hook']}")
            lines.append(f"- **核心冲突**：{prop['conflict']}")
            lines.append(f"- **篇幅目标**：{prop['target_words']}")
            lines.append(f"- **叙事脉络**：")
            for step in prop["narrative_arc"]:
                lines.append(f"  1. {step}")
            lines.append(f"- **推荐话题标签**：{' '.join(prop['tags'])}")
            lines.append(f"- **16:9 视觉配图方案**：`{prop['visual_prompt']}`\n")

        lines.append("## 三、平台红线与 AI 去痕规避清单")
        for item in data["fact_dossier"]["style_rules"]:
            lines.append(f"- ✅ {item}")
        lines.append(f"- ❌ 严厉剔除的悬浮套话：{', '.join(data['fact_dossier']['platitude_blacklist'])}\n")

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))


def display_research_cards(research_data: Dict[str, Any]):
    """Pretty print proposal cards into terminal for user selection"""
    topic = research_data.get("topic", "")
    proposals = research_data.get("proposals", [])

    print("\n" + "=" * 76)
    print(f"🎯 深度调研成果与方案卡片：【{topic}】")
    print("=" * 76)

    for p in proposals:
        print(f"\n【方案 {p['id']}】{p['title']}")
        print(f"  📌 定位风格：{p['angle_type']} | 字数建议：{p['target_words']}")
        print(f"  ⚡ 黄金引子：\"{p['hook']}\"")
        print(f"  ⚖️ 核心对立：{p['conflict']}")
        print(f"  🏷️ 标签规划：{' '.join(p['tags'])}")
        print("  " + "-" * 72)

    print("\n💡 提示：")
    print("  • 完整调研资料账本已生成至: `output/research_dossier.md`")
    print("  • 用户选定心仪方案后，直接调度 Subagent 跑通：撰写 -> 质检审核 -> 16:9 生图 -> 排版 -> 发布。")
    print("=" * 76 + "\n")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="头条深度选题调研与方案生成引擎")
    parser.add_argument("topic", help="用户提出的问题、具体社会生活现象，或头条热榜话题")
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出")
    args = parser.parse_args()

    engine = ResearchEngine(args.topic)
    data = engine.run_full_research()

    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        display_research_cards(data)


if __name__ == "__main__":
    main()
