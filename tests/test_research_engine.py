import pytest
from pathlib import Path
from scripts.research_engine import ResearchEngine


def test_research_engine_topic_cleaning():
    engine = ResearchEngine("#生活里，该依靠自己还是依靠他人？#")
    assert engine.clean_topic == "生活里，该依靠自己还是依靠他人"


def test_research_engine_perspectives():
    engine = ResearchEngine("为什么现在的年轻人热衷去社区食堂？")
    perspectives = engine.analyze_perspectives()
    assert len(perspectives) == 4
    names = [p["name"] for p in perspectives]
    assert "经济与民生账本" in names
    assert "反常识与底层洞察" in names


def test_research_engine_proposals():
    engine = ResearchEngine("年少吃苦和年老吃苦，哪一个更苦？")
    proposals = engine.synthesize_proposals()
    assert len(proposals) >= 4
    for p in proposals:
        assert "title" in p
        assert "hook" in p
        assert "conflict" in p
        assert "target_words" in p
        assert len(p["tags"]) >= 2
        # Title length should be suitable for Toutiao (under 30 chars)
        assert len(p["title"]) <= 30


def test_research_engine_full_run(tmp_path, monkeypatch):
    engine = ResearchEngine("人到中年为什么最没有底气？")
    data = engine.run_full_research()
    assert "topic" in data
    assert "perspectives" in data
    assert "proposals" in data
    assert "fact_dossier" in data
