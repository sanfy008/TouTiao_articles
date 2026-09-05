import pytest
from scripts.scout_trends import parse_metric_to_number, format_heat


def test_parse_metric_to_number():
    assert parse_metric_to_number("101.6万") == 1016000.0
    assert parse_metric_to_number("1.2亿") == 120000000.0
    assert parse_metric_to_number("3,500") == 3500.0
    assert parse_metric_to_number("894") == 894.0
    assert parse_metric_to_number("") == 0.0
    assert parse_metric_to_number("无数据") == 0.0


def test_format_heat():
    assert format_heat(1250000000) == "12.5亿"
    assert format_heat(1016000) == "101.6万"
    assert format_heat(894) == "894"
