"""DB 없이 SQL 생성과 사용자 입력 파라미터 전달을 검증하는 단위 테스트."""

import importlib
import sys
from pathlib import Path
from types import ModuleType

import pytest


@pytest.fixture
def queries(monkeypatch):
    """MySQL 없이 모듈을 불러오고 run()을 기록한다."""
    app_dir = Path(__file__).resolve().parents[1] / "app"
    monkeypatch.syspath_prepend(str(app_dir))
    fake_pymysql = ModuleType("pymysql")
    fake_config = ModuleType("config")
    fake_config.DB = {}
    monkeypatch.setitem(sys.modules, "pymysql", fake_pymysql)
    monkeypatch.setitem(sys.modules, "config", fake_config)
    sys.modules.pop("queries", None)
    module = importlib.import_module("queries")
    recorded = []

    def fake_run(sql, params=()):
        recorded.append((sql, list(params)))
        return ["테스트"], [("값",)]

    monkeypatch.setattr(module, "run", fake_run)
    module._recorded = recorded
    yield module
    sys.modules.pop("queries", None)


def assert_valid_join(sql):
    assert "h.sgg_code" not in sql
    if "JOIN region r" in sql:
        assert "h.region_id = r.region_id" in sql


@pytest.mark.parametrize(
    "function,args,expected",
    [
        ("search_hospital", {"sido": "서울", "sgg": "강남구", "htype": "의원", "name": "연세"}, ["서울", "강남구", "의원", "%연세%"]),
        ("find_by_dept", {"dept": "내과", "sido": "서울", "sgg": "강남구"}, ["내과", "서울", "강남구"]),
        ("dept_stats_by_region", {"sido": "서울", "dept": "내과"}, ["서울", "내과"]),
        ("hospital_detail", {"name": "연세"}, ["%연세%"]),
        ("top_specialists", {"dept": "내과", "sido": "서울", "n": 10}, ["내과", "서울", 10]),
        ("type_stats", {"sido": "서울"}, ["서울"]),
        ("many_depts", {"sgg": "강남구", "min_cnt": 2, "sido": "서울"}, ["강남구", "서울", 2]),
        ("no_dept_regions", {"sido": "서울", "dept": "피부과"}, ["서울", "피부과"]),
    ],
)
def test_all_eight_features_use_correct_sql(queries, function, args, expected):
    getattr(queries, function)(**args)
    sql, params = queries._recorded[-1]
    assert_valid_join(sql)
    assert params == expected
    assert sql.count("%s") == len(expected)


def test_f1_optional_filters(queries):
    queries.search_hospital(name="%') OR 1=1 --")
    sql, params = queries._recorded[-1]
    assert sql.count("%s") == 1
    assert "OR 1=1" not in sql
    assert params == ["%%') OR 1=1 --%"]
    assert_valid_join(sql)


def test_e4_optional_sido(queries):
    queries.many_depts("강남구", 3)
    sql, params = queries._recorded[-1]
    assert "r.sido = %s" not in sql
    assert params == ["강남구", 3]


def test_f3_has_aggregation(queries):
    queries.dept_stats_by_region("서울", "내과")
    sql, _ = queries._recorded[-1]
    for part in ("COUNT(DISTINCT", "SUM(", "GROUP BY"):
        assert part in sql


def test_e5_has_not_exists_and_correct_region_key(queries):
    queries.no_dept_regions("서울", "내과")
    sql, _ = queries._recorded[-1]
    assert "NOT EXISTS" in sql
    assert "h.region_id = r.region_id" in sql


@pytest.mark.parametrize("n", [0, -1, 101])
def test_top_n_rejects_out_of_range(queries, n):
    with pytest.raises(ValueError):
        queries.top_specialists("내과", "서울", n)


def test_distinct_values(queries):
    # run()을 목록 형태로 모킹한 경우 선택값만 추출하는지 확인
    assert queries.distinct_values("sgg") == ["값"]
    with pytest.raises(ValueError):
        queries.distinct_values("invalid")