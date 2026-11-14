"""병원 찾기 콘솔 프로그램: 메뉴, 조건 입력, 표 출력, 오류 처리."""

import sys

try:
    import pymysql
    from tabulate import tabulate
except ImportError as exc:
    sys.exit(
        f"라이브러리가 설치되지 않았습니다: {exc.name}\n"
        "프로젝트 최상위 폴더에서 python -m pip install -r requirements.txt"
    )

try:
    import queries
except ModuleNotFoundError as exc:
    if exc.name == "config":
        sys.exit(
            "app/config.py가 없습니다. app/config_example.py를 복사해서 "
            "config.py로 만들고 MySQL 비밀번호를 설정하세요."
        )
    raise

# (함수 인수명, 입력 안내, 필수 여부, 자료형, '?' 목록 종류)
SIDO = ("sido", "시도 (예: 서울)", True, str, "sido")
SIDO_OPT = ("sido", "시도 (예: 서울)", False, str, "sido")
SGG = ("sgg", "시군구 (예: 강남구)", True, str, "sgg")
SGG_OPT = ("sgg", "시군구 (예: 강남구)", False, str, "sgg")
TYPE_OPT = ("htype", "종별 (예: 의원)", False, str, "type")
NAME = ("name", "병원명 일부", True, str, None)
NAME_OPT = ("name", "병원명 일부", False, str, None)
DEPT = ("dept", "진료과목 (예: 내과)", True, str, "dept")
TOP_N = ("n", "조회할 병원 수 N (1~100)", True, int, None)
MIN_CNT = ("min_cnt", "최소 진료과목 수", True, int, None)

# 번호: (이름, 함수, 입력 항목들, 최대 표시 행 수 또는 None)
FEATURES = {
    "1": ("병원 검색", queries.search_hospital, [SIDO_OPT, SGG_OPT, TYPE_OPT, NAME_OPT], 50),
    "2": ("진료과목으로 병원 찾기", queries.find_by_dept, [DEPT, SIDO, SGG_OPT], 100),
    "3": ("지역별 진료과목 현황", queries.dept_stats_by_region, [SIDO, DEPT], None),
    "4": ("병원 상세 (진료과목 목록)", queries.hospital_detail, [NAME], 30),
    "5": ("전문의가 많은 병원 TOP N", queries.top_specialists, [DEPT, SIDO, TOP_N], None),
    "6": ("종별 병원 수 통계", queries.type_stats, [SIDO], None),
    "7": ("진료과목이 많은 병원", queries.many_depts, [SGG, MIN_CNT, SIDO_OPT], 100),
    "8": ("특정 과목 병원이 없는 지역", queries.no_dept_regions, [SIDO, DEPT], None),
}


def print_menu():
    print("\n========== 병원 찾기 ==========")
    for key, (title, _, _, _) in FEATURES.items():
        print(f" {key}. {title}")
    print(" 0. 종료")
    print("===============================")


def show_choices(kind):
    values = queries.distinct_values(kind)
    if values:
        print("  선택 가능:", ", ".join(str(v) for v in values))
    else:
        print("  선택 가능한 값이 없습니다.")


def ask(field):
    """필수 입력 검증과 선택 입력 생략, '?' 목록 확인을 처리한다."""
    key, label, required, kind, choices = field
    hint = "" if required else " [생략: Enter]"
    if choices:
        hint += " [목록: ?]"
    while True:
        raw = input(f"  {label}{hint}: ").strip()
        if raw == "?" and choices:
            show_choices(choices)
            continue
        if not raw:
            if required:
                print("  필수 입력입니다.")
                continue
            return None
        if kind is int:
            if raw.isdecimal() and int(raw) > 0:
                number = int(raw)
                if key == "n" and number > 100:
                    print("  TOP N은 최대 100까지 가능합니다.")
                    continue
                return number
            print("  1 이상의 정수를 입력하세요.")
            continue
        return raw


def show(cols, rows, limit=None, feature=None):
    if not rows:
        print("\n조건에 맞는 결과가 없습니다.")
        return
    print()
    # 긴 주소와 진료과목 목록을 셀 안에서 줄바꿈한다.
    # 나머지 기능의 표 출력 방식은 유지한다.
    column_widths = {
        "1": {"병원명": 24, "종별": 10, "시도": 8, "시군구": 10, "주소": 34, "전화": 15},
        "4": {"병원명": 24, "종별": 10, "주소": 36, "진료과목": 42},
    }
    widths = column_widths.get(feature)
    options = {}
    if widths:
        options["maxcolwidths"] = [widths.get(col) for col in cols]
        options["disable_numparse"] = True
    print(tabulate(rows, headers=cols, tablefmt="simple_grid", **options))
    if limit is None:
        print(f"표시된 결과: {len(rows)}건")
    else:
        print(f"표시된 결과: {len(rows)}건 (최대 {limit}건까지 출력)")


def run_feature(key):
    title, func, fields, limit = FEATURES[key]
    print(f"\n[{title}]")
    args = {field[0]: ask(field) for field in fields}
    show(*func(**args), limit=limit, feature=key)


def main():
    while True:
        print_menu()
        menu = input("메뉴 선택: ").strip()
        if menu == "0":
            print("프로그램을 종료합니다.")
            return
        if menu not in FEATURES:
            print("메뉴 번호를 다시 입력하세요.")
            continue
        try:
            run_feature(menu)
        except pymysql.err.OperationalError as exc:
            print("MySQL 연결 오류: 서버 실행 여부와 app/config.py를 확인하세요.", exc)
        except pymysql.MySQLError as exc:
            print("SQL 실행 오류:", exc)
        except ValueError as exc:
            print("입력 오류:", exc)
        except Exception as exc:
            print("예기치 않은 오류:", exc)
        input("\n(Enter를 누르면 메뉴로 돌아갑니다)")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\n프로그램을 종료합니다.")