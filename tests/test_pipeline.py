# -*- coding: utf-8 -*-
import pytest
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
