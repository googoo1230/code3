"""콘솔 UI의 주요 흐름을 실제 DB 없이 검증한다."""

import importlib
import sys
from pathlib import Path
from types import ModuleType

import pytest


@pytest.fixture
def main_module(monkeypatch):
    app_dir = Path(__file__).resolve().parents[1] / "app"
    monkeypatch.syspath_prepend(str(app_dir))
    fake_pymysql = ModuleType("pymysql")
    class MySQLError(Exception):
        pass
    class OperationalError(MySQLError):
        pass
    fake_pymysql.MySQLError = MySQLError
    fake_pymysql.err = ModuleType("pymysql.err")
    fake_pymysql.err.OperationalError = OperationalError
    fake_queries = ModuleType("queries")
    for fn in ["search_hospital", "find_by_dept", "dept_stats_by_region", "hospital_detail", "top_specialists", "type_stats", "many_depts", "no_dept_regions"]:
        setattr(fake_queries, fn, lambda **kw: (["테스트"], [("결과",)]))
    fake_queries.distinct_values = lambda kind: ["서울", "경기"]
    monkeypatch.setitem(sys.modules, "pymysql", fake_pymysql)
    monkeypatch.setitem(sys.modules, "queries", fake_queries)
    sys.modules.pop("main", None)
    module = importlib.import_module("main")
    yield module
    sys.modules.pop("main", None)


def test_menu_has_eight_features(main_module, capsys):
    main_module.print_menu()
    output = capsys.readouterr().out
    assert "1. 병원 검색" in output
    assert "8. 특정 과목 병원이 없는 지역" in output
    assert "0. 종료" in output


def test_optional_input_can_be_skipped(main_module, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "")
    assert main_module.ask(main_module.SIDO_OPT) is None


def test_question_mark_displays_choices(main_module, monkeypatch, capsys):
    values = iter(["?", "서울"])
    monkeypatch.setattr("builtins.input", lambda _: next(values))
    assert main_module.ask(main_module.SIDO) == "서울"
    assert "선택 가능" in capsys.readouterr().out


def test_top_n_validation(main_module, monkeypatch, capsys):
    values = iter(["101", "5"])
    monkeypatch.setattr("builtins.input", lambda _: next(values))
    assert main_module.ask(main_module.TOP_N) == 5
    assert "최대 100" in capsys.readouterr().out


def test_search_results_explain_display_limit(main_module, capsys):
    main_module.show(["병원명"], [("테스트의원",)], limit=50)
    assert "최대 50건까지 출력" in capsys.readouterr().out


def test_exit_without_query(main_module, monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda _: "0")
    main_module.main()
    assert "프로그램을 종료합니다" in capsys.readouterr().out