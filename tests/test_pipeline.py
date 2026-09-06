import time
from scripts.pipeline import ContentAuditor, prepare_article_directory


def test_auditor_char_count_pass():
    # 22 chars * 24 = 528 Chinese characters
    unit = "生活就是这样，关起门来过好自己的日子比什么都强。"
    text = unit * 24
    title = "生活过好自己的日子才是底气"
    passed, issues, metrics = ContentAuditor.audit(title, text)
    assert passed is True
    assert metrics["char_count"] >= 480
    assert metrics["char_count"] <= 620


def test_auditor_char_count_too_short():
    text = "短文测试"
    title = "短文"
    passed, issues, metrics = ContentAuditor.audit(title, text)
    assert passed is False
    assert any("字数过少" in i for i in issues)


def test_auditor_platitude_detected():
    unit = "生活就是这样，关起门来过好自己的日子比什么都强。"
    text = "在这个快节奏的时代，" + unit * 24
    title = "生活过好自己的日子才是底气"
    passed, issues, metrics = ContentAuditor.audit(title, text)
    assert passed is False
    assert any("悬浮 AI 套话" in i for i in issues)


def test_auditor_logic_number_consistency():
    unit = "生活就是这样，关起门来过好自己的日子比什么都强。"
    # Title promises 3 words, body has exact 3 words and passes length check (531 chars)
    title = "其实就这三个字"
    text_ok = "走过半生才明白，这三个字：靠自己。" + unit * 24
    passed, issues, _ = ContentAuditor.audit(title, text_ok)
    assert passed is True

    # Title promises 3 words, body fails to supply it
    text_fail = "走过半生才明白，其实要坚强点。" + unit * 24
    passed, issues, _ = ContentAuditor.audit(title, text_fail)
    assert passed is False
    assert any("逻辑一致性警告" in i for i in issues)


def test_auditor_hashtag_warning():
    unit = "生活就是这样，关起门来过好自己的日子比什么都强。"
    text = unit * 24 + "\n\n## 话题\n#生活#\n"
    title = "测试标题"
    passed, issues, _ = ContentAuditor.audit(title, text)
    assert passed is False
    assert any("## 话题" in i for i in issues)


def test_prepare_article_directory_structure(tmp_path):
    now = time.localtime()
    expected_month = f"{now.tm_mon:02d}"
    expected_day = f"{now.tm_mday:02d}"

    title = "测试文章标题：如何过好这一生？"
    content = "# 测试文章标题\n\n正文内容测试。"

    # Create dummy cover image
    dummy_cover = tmp_path / "dummy_cover.jpg"
    dummy_cover.write_bytes(b"dummy image bytes")

    target_dir = prepare_article_directory(
        title=title,
        content=content,
        cover_source=str(dummy_cover),
        base_dir=tmp_path / "articles",
    )

    assert target_dir.exists()
    assert target_dir.parent.name == expected_day
    assert target_dir.parent.parent.name == expected_month
    assert (target_dir / "article.md").exists()
    assert (target_dir / "article.md").read_text(encoding="utf-8") == content
    assert (target_dir / "cover.jpg").exists()
    assert (target_dir / "cover.jpg").read_bytes() == b"dummy image bytes"


def test_auditor_astra_bullet_points_rejected():
    base_para = "很多人总觉得别人的生活更加精彩，其实关起门来过日子，柴米油盐的滋味家家户户都一样平凡真实。大家都在为了碎银几两奔波劳碌。"
    paras = [base_para] * 9
    body_with_bullets = (
        "\n\n".join(paras[:4])
        + "\n\n- 这是第一条列表项内容，不符合散文规范\n- 这是第二条列表项内容\n\n"
        + "\n\n".join(paras[4:])
    )
    title = "自然散文测试标题"
    passed, issues, _ = ContentAuditor.audit(title, body_with_bullets)
    assert passed is False
    assert any("bullet points" in i for i in issues)


def test_auditor_astra_long_paragraph_rejected():
    base_para = "很多人总觉得别人的生活更加精彩，其实关起门来过日子，柴米油盐的滋味家家户户都一样平凡真实。大家都在为了碎银几两奔波劳碌。"
    long_para = "生活就是这样，关起门来过好自己的日子比什么都强。" * 6  # 132 chars > 110
    body = "\n\n".join([base_para] * 7 + [long_para])
    title = "长段落检测标题"
    passed, issues, _ = ContentAuditor.audit(title, body)
    assert passed is False
    assert any("存在段落过长" in i for i in issues)


def test_auditor_astra_contrastive_framing_rejected():
    paras = [
        "很多人总觉得别人的生活更加精彩，其实关起门来过日子，柴米油盐的滋味家家户户都一样平凡真实。这不是偶然的巧合，而是必然的生活规律。",
        "年轻的时候总想着证明给全世界看，走过不少弯路之后才逐渐明白，冷暖自知才是人生最朴素的真理。不仅是对个人的考验，更是对心性的磨砺。",
        "每天早出晚归忙忙碌碌，最踏实的时刻莫过于推开家门闻到厨房饭菜香气的那一瞬间。表面上大家在争论快慢，实际上大家真正在意的是终点。",
        "在日常生活中遇到难事不要急着找人诉苦，冷静下来把手头能做的事情一件件理顺分明，按部就班去解决。抱怨解决不了任何现实问题。",
        "银行卡里的存款数字不在于有多么惊人，关键在于每一分辛苦积攒的积蓄都能让人在面对突发意外时多一份从容。手里有粮心里才不慌。",
        "平时少去琢磨那些不切实际的高谈阔论，脚踏实地把眼前的工作做好，按时拿到属于自己的劳动报酬才是最稳妥的。踏实做事比什么都强。",
        "身体健康永远排在人生的第一位，早睡早起按时吃饭，远比任何廉价的深夜焦虑和胡思乱想管用得多。照顾好身体是做一切事情的前提。",
        "人与人之间的日常交往最讲究分寸感，不打扰别人的宁静，也不强求别人的理解，各自安好便足够舒心。保持界限感才能长久相处。",
        "把所有精力和注意力彻底收回到自己和家人身上，用心过好当下的柴米油盐，这就是对岁月最好的交代和答卷。平淡之中自有真味。",
    ]
    body = "\n\n".join(paras)
    title = "过好自己的日子才是真正的底气"
    passed, issues, _ = ContentAuditor.audit(title, body)
    assert passed is False
    assert any("机械对仗 AI 腔" in i for i in issues)


def test_auditor_astra_natural_prose_passed():
    paras = [
        "很多人总觉得别人的生活更加精彩，其实关起门来过日子，柴米油盐的滋味家家户户都一样平凡真实。大家都在为了碎银几两奔波劳碌。",
        "年轻的时候总想着证明给全世界看，走过不少弯路之后才逐渐明白，冷暖自知才是人生最朴素的真理。很多时候沉默胜过所有的解释。",
        "每天早出晚归忙忙碌碌，最踏实的时刻莫过于推开家门闻到厨房饭菜香气的那一瞬间，心里特别踏实温暖。一碗热汤胜过千言万语。",
        "在日常生活中遇到难事不要急着找人诉苦，冷静下来把手头能做的事情一件件理顺分明，按部就班去解决。抱怨解决不了任何现实问题。",
        "银行卡里的存款数字不在于有多么惊人，关键在于每一分辛苦积攒的积蓄都能让人在面对突发意外时多一份从容。手里有粮心里才不慌。",
        "平时少去琢磨那些不切实际的高谈阔论，脚踏实地把眼前的工作做好，按时拿到属于自己的劳动报酬才是最稳妥的。踏实做事比什么都强。",
        "身体健康永远排在人生的第一位，早睡早起按时吃饭，远比任何廉价的深夜焦虑和胡思乱想管用得多。照顾好身体是做一切事情的前提。",
        "人与人之间的日常交往最讲究分寸感，不打扰别人的宁静，也不强求别人的理解，各自安好便足够舒心。保持界限感才能长久相处。",
        "把所有精力和注意力彻底收回到自己和家人身上，用心过好当下的柴米油盐，这就是对岁月最好的交代和答卷。平淡之中自有真味。",
    ]
    body = "\n\n".join(paras)
    title = "过好自己的日子才是真正的底气"
    passed, issues, metrics = ContentAuditor.audit(title, body)
    assert passed is True
    assert metrics["passed"] is True
    assert metrics["paragraph_count"] == 9
    assert 480 <= metrics["char_count"] <= 620

