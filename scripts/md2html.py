import re
from dataclasses import dataclass
from pathlib import Path

import markdown as markdown_lib


IMAGE_PATTERN = re.compile(
    r"!\[([^\]]*)\]\(\s*"
    r"(?:<([^>]+)>|((?:\\.|[^()\s]|\([^)]*\))+))"
    r"(?:\s+[\"'][^\"']*[\"'])?\s*\)"
)
FENCE_PATTERN = re.compile(r"^\s*(`{3,}|~{3,})")


@dataclass
class ConvertedMarkdown:
    html: str
    images: list[dict[str, str]]


def _resolve_image_path(raw_path, base_dir):
    cleaned = raw_path.strip().strip("<>").strip("\"'")
    if cleaned.startswith(("http://", "https://", "data:")):
        return cleaned
    base = Path(base_dir or ".")
    image_path = Path(cleaned)
    if not image_path.is_absolute():
        image_path = base / image_path
    return str(image_path.resolve())


def _replace_markdown_images(line, images, base_dir):
    def replace(match):
        placeholder = f"TTIMGPH_{len(images)}"
        raw_path = match.group(2) or match.group(3)
        images.append(
            {
                "placeholder": placeholder,
                "path": _resolve_image_path(raw_path, base_dir),
                "alt": match.group(1).strip(),
            }
        )
        return placeholder

    return IMAGE_PATTERN.sub(replace, line)


def _extract_images(text, base_dir):
    images = []
    converted_lines = []
    fence_character = None
    fence_length = 0

    for line in text.splitlines():
        fence_match = FENCE_PATTERN.match(line)
        if fence_match:
            marker = fence_match.group(1)
            if fence_character is None:
                fence_character = marker[0]
                fence_length = len(marker)
            elif marker[0] == fence_character and len(marker) >= fence_length:
                fence_character = None
                fence_length = 0
            converted_lines.append(line)
            continue
        converted_lines.append(
            line
            if fence_character is not None
            else _replace_markdown_images(line, images, base_dir)
        )

    return "\n".join(converted_lines), images


def strip_frontmatter(text: str) -> str:
    """Strip YAML frontmatter if present."""
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        for idx in range(1, len(lines)):
            if lines[idx].strip() == "---":
                return "\n".join(lines[idx + 1 :]).lstrip()
    return text


TOPIC_HEADING_PATTERN = re.compile(r"^#{1,6}\s*(话题|话题推荐|推荐话题|话题讨论|标签|热门标签)\s*$")
HASHTAG_LINE_PATTERN = re.compile(r"^#[^#\s\n]+#")


def normalize_topics(text: str) -> str:
    """
    Normalize topic/hashtag blocks to prevent Markdown from treating them as headings.
    For example:
        ## 话题
        #广州餐饮# #老字号闭店#
    will be converted to:
        \\#广州餐饮# #老字号闭店#
    so that it renders as a regular <p> paragraph with pure hashtags (#tag1# #tag2#)
    without any '话题：' prefix and without triggering Toutiao's H1/H2 title styles.
    """
    lines = text.splitlines()
    normalized = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # 1. Topic heading like '## 话题' or '## 话题推荐'
        if TOPIC_HEADING_PATTERN.match(stripped):
            next_idx = i + 1
            while next_idx < len(lines) and not lines[next_idx].strip():
                next_idx += 1
            if next_idx < len(lines) and re.search(r"#[^#\s\n]+#", lines[next_idx]):
                target_line = lines[next_idx].strip()
                # Strip any existing '话题：' prefix if present
                target_line = re.sub(r"^(话题|标签|话题讨论|推荐话题)[：:]\s*", "", target_line)
                if target_line.startswith("#"):
                    target_line = "\\" + target_line
                normalized.append("")
                normalized.append(target_line)
                i = next_idx + 1
                continue

        # 2. Line that has a '话题：' prefix followed by hashtags
        if re.match(r"^(话题|标签|话题讨论|推荐话题)[：:]\s*#", stripped):
            target_line = re.sub(r"^(话题|标签|话题讨论|推荐话题)[：:]\s*", "", stripped)
            if target_line.startswith("#"):
                target_line = "\\" + target_line
            normalized.append(target_line)
            i += 1
            continue

        # 3. Line starting directly with a hashtag (which Markdown would parse as H1)
        if HASHTAG_LINE_PATTERN.match(stripped):
            normalized.append("\\" + stripped)
            i += 1
            continue

        normalized.append(line)
        i += 1

    return "\n".join(normalized)


def convert_with_images(text, base_dir=None):
    """
    Convert common blog Markdown to HTML while preserving image positions.
    """
    clean_text = strip_frontmatter(text)
    clean_text = normalize_topics(clean_text)
    prepared_text, images = _extract_images(clean_text, base_dir)
    html = markdown_lib.markdown(
        prepared_text,
        extensions=["extra", "sane_lists"],
        output_format="html5",
    )
    return ConvertedMarkdown(html=html, images=images)


def convert(text):
    return convert_with_images(text).html


if __name__ == "__main__":
    # Test
    sample = """# Title
    
    Introduction **bold**.
    
    * Item 1
    * Item 2
    
    ```python
    print("Code")
    ```
    """
    print(convert(sample))
