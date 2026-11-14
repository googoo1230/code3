"""병원 찾기 프로젝트의 MySQL 조회 함수.

실제 hospital_db.sql 스키마를 사용한다.
- hospital.region_id -> region.region_id (지역 JOIN)
- 사용자 입력은 반드시 %s 파라미터로 전달한다.
- 모든 함수의 반환값: (컬럼명 리스트, 결과 행 목록)
"""

import pymysql
from config import DB


def run(sql, params=()):
    """SQL을 실행하고 (컬럼명, 행 목록)을 반환한다. 항상 연결을 닫는다."""
    conn = pymysql.connect(**DB)
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            cols = [c[0] for c in cur.description]
            return cols, cur.fetchall()
    finally:
        conn.close()


def _add(where, params, condition, value):
    """선택적으로 입력한 조건만 WHERE와 파라미터에 추가한다."""
    if value is not None and value != "":
        where.append(condition)
        params.append(value)


# ─────────────────── 기본 기능 (F1~F3) ───────────────────

def search_hospital(sido=None, sgg=None, htype=None, name=None):
    """F1: 시도, 시군구, 종별, 병원명 중 입력한 조건을 모두 적용한다."""
    where, params = [], []
    _add(where, params, "r.sido = %s", sido)
    _add(where, params, "r.sgg = %s", sgg)
    _add(where, params, "h.type = %s", htype)
    _add(where, params, "h.name LIKE %s", f"%{name}%" if name else None)

    sql = (
        "SELECT h.name AS 병원명, h.type AS 종별, r.sido AS 시도, "
        "r.sgg AS 시군구, h.address AS 주소, h.tel AS 전화 "
        "FROM hospital h "
        "JOIN region r ON h.region_id = r.region_id "
    )
    if where:
        sql += "WHERE " + " AND ".join(where) + " "
    sql += "ORDER BY h.name, h.ykiho LIMIT 50"
    return run(sql, params)


def find_by_dept(dept, sido, sgg=None):
    """F2: 진료과목, 시도, 선택적 시군구로 병원을 찾는다."""
    where, params = ["d.dept_name = %s", "r.sido = %s"], [dept, sido]
    _add(where, params, "r.sgg = %s", sgg)
    sql = (
        "SELECT h.name AS 병원명, h.type AS 종별, r.sgg AS 시군구, "
        "hd.specialist_cnt AS 전문의수, h.tel AS 전화 "
        "FROM hospital h "
        "JOIN hospital_dept hd ON h.ykiho = hd.ykiho "
        "JOIN department d ON hd.dept_code = d.dept_code "
        "JOIN region r ON h.region_id = r.region_id "
        "WHERE " + " AND ".join(where) + " "
        "ORDER BY hd.specialist_cnt DESC, h.name, h.ykiho LIMIT 100"
    )
    return run(sql, params)


def dept_stats_by_region(sido, dept):
    """F3: 시군구별 해당 과목 병원 수와 전문의 수 합계를 집계한다."""
    sql = (
        "SELECT r.sgg AS 시군구, COUNT(DISTINCT h.ykiho) AS 병원수, "
        "COALESCE(SUM(hd.specialist_cnt), 0) AS 전문의합계 "
        "FROM hospital h "
        "JOIN hospital_dept hd ON h.ykiho = hd.ykiho "
        "JOIN department d ON hd.dept_code = d.dept_code "
        "JOIN region r ON h.region_id = r.region_id "
        "WHERE r.sido = %s AND d.dept_name = %s "
        "GROUP BY r.region_id, r.sgg "
        "ORDER BY 병원수 DESC, r.sgg"
    )
    return run(sql, (sido, dept))


# ─────────────────── 추가 기능 (E1~E5) ───────────────────

def hospital_detail(name):
    """E1: 병원명 검색 후 진료과목을 모아서 보여준다."""
    sql = (
        "SELECT h.name AS 병원명, h.type AS 종별, h.address AS 주소, "
        "GROUP_CONCAT(d.dept_name ORDER BY d.dept_name SEPARATOR ', ') AS 진료과목 "
        "FROM hospital h "
        "LEFT JOIN hospital_dept hd ON h.ykiho = hd.ykiho "
        "LEFT JOIN department d ON hd.dept_code = d.dept_code "
        "WHERE h.name LIKE %s "
        "GROUP BY h.ykiho, h.name, h.type, h.address "
        "ORDER BY h.name, h.ykiho LIMIT 30"
    )
    return run(sql, (f"%{name}%",))


def top_specialists(dept, sido, n):
    """E2: 특정 과목, 지역의 전문의 수 TOP N (최대 100)."""
    n = int(n)
    if not 1 <= n <= 100:
        raise ValueError("TOP N은 1부터 100 사이로 입력하세요.")
    sql = (
        "SELECT h.name AS 병원명, r.sgg AS 시군구, "
        "hd.specialist_cnt AS 전문의수 "
        "FROM hospital h "
        "JOIN hospital_dept hd ON h.ykiho = hd.ykiho "
        "JOIN department d ON hd.dept_code = d.dept_code "
        "JOIN region r ON h.region_id = r.region_id "
        "WHERE d.dept_name = %s AND r.sido = %s "
        "ORDER BY hd.specialist_cnt DESC, h.name, h.ykiho LIMIT %s"
    )
    return run(sql, (dept, sido, n))


def type_stats(sido):
    """E3: 시도별 병원 종별 개수."""
    sql = (
        "SELECT h.type AS 종별, COUNT(*) AS 병원수 "
        "FROM hospital h JOIN region r ON h.region_id = r.region_id "
        "WHERE r.sido = %s GROUP BY h.type ORDER BY 병원수 DESC, h.type"
    )
    return run(sql, (sido,))


def many_depts(sgg, min_cnt, sido=None):
    """E4: 시군구 내 진료과목이 일정 개수 이상인 병원.

    같은 시군구명이 다른 시도에도 존재할 수 있으므로 시도도 선택적으로 받는다.
    """
    min_cnt = int(min_cnt)
    if min_cnt < 1:
        raise ValueError("최소 진료과목 수는 1 이상이어야 합니다.")
    where, params = ["r.sgg = %s"], [sgg]
    _add(where, params, "r.sido = %s", sido)
    sql = (
        "SELECT h.name AS 병원명, h.type AS 종별, r.sido AS 시도, "
        "r.sgg AS 시군구, COUNT(*) AS 과목수 "
        "FROM hospital h "
        "JOIN hospital_dept hd ON h.ykiho = hd.ykiho "
        "JOIN region r ON h.region_id = r.region_id "
        "WHERE " + " AND ".join(where) + " "
        "GROUP BY h.ykiho, h.name, h.type, r.sido, r.sgg "
        "HAVING COUNT(*) >= %s "
        "ORDER BY 과목수 DESC, h.name, h.ykiho LIMIT 100"
    )
    params.append(min_cnt)
    return run(sql, params)


def no_dept_regions(sido, dept):
    """E5: region에 등록되어 있지만 해당 과목 병원이 없는 시군구."""
    sql = (
        "SELECT r.sido AS 시도, r.sgg AS 시군구 "
        "FROM region r "
        "WHERE r.sido = %s "
        "AND NOT EXISTS ("
        "SELECT 1 FROM hospital h "
        "JOIN hospital_dept hd ON h.ykiho = hd.ykiho "
        "JOIN department d ON hd.dept_code = d.dept_code "
        "WHERE h.region_id = r.region_id AND d.dept_name = %s"
        ") ORDER BY r.sgg"
    )
    return run(sql, (sido, dept))


# ─────────────────── 입력 도우미 ───────────────────

def distinct_values(kind):
    """실제 DB에서 선택할 수 있는 시도/시군구/종별/진료과목을 가져온다."""
    sql_by_kind = {
        "sido": "SELECT DISTINCT sido FROM region ORDER BY sido",
        "sgg": "SELECT DISTINCT sgg FROM region ORDER BY sgg",
        "type": "SELECT DISTINCT type FROM hospital ORDER BY type",
        "dept": "SELECT dept_name FROM department ORDER BY dept_name",
    }
    if kind not in sql_by_kind:
        raise ValueError("지원하지 않는 목록입니다.")
    _, rows = run(sql_by_kind[kind])
    return [row[0] for row in rows]