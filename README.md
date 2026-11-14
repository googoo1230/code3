# 병원·진료과목 찾기 (6조)

전국 병원 공공데이터를 MySQL에서 조회하는 **Python 콘솔 프로그램**입니다. `googoo1230/code2`의 기존 코드를 바탕으로 제공된 `hospital_db.sql`의 **실제 테이블 구조**에 맞게 수정했습니다.

## 주요 기능

| 번호 | 조회 기능 | SQL 특징 |
|---|---|---|
| 1 | 병원 검색 | 시도·시군구·종별·병원명 다중 조건 / JOIN |
| 2 | 진료과목으로 병원 찾기 | 4개 테이블 JOIN |
| 3 | 지역별 진료과목 현황 | 4개 테이블 JOIN / COUNT / SUM / GROUP BY |
| 4 | 병원 상세: 진료과목 목록 | LEFT JOIN / GROUP_CONCAT |
| 5 | 전문의 많은 병원 TOP N | ORDER BY / LIMIT |
| 6 | 종별 병원 수 통계 | GROUP BY / COUNT |
| 7 | 진료과목이 많은 병원 | GROUP BY / HAVING |
| 8 | 해당 진료과목 병원이 없는 지역 | NOT EXISTS |

기본 기능: 1~3번. 추가 기능: 4~8번.

## 1. 실행 환경

- Python 3.10 이상 권장
- MySQL 8.0 (제공된 SQL 덤프는 MySQL 8.0.46에서 생성)
- `hospital_db.sql` 원본 파일(팀원에게 별도로 전달받음)

```bash
python -m pip install -r requirements.txt
```

## 2. MySQL 데이터베이스 복원

**`hospital_db.sql`에는 `CREATE DATABASE hospital_db`, `USE hospital_db`, 테이블 정의, 데이터 INSERT가 모두 포함**되어 있어 별도 CSV 적재가 필요하지 않습니다.

MySQL Workbench에서는 **Server → Data Import → Import from Self-Contained File**을 선택하고 `hospital_db.sql`을 지정해 복원할 수 있습니다. 파일에 DB 생성 구문이 있으므로 MySQL 환경에 따라 Workbench 복원 옵션을 조정해야 할 수 있습니다.

Windows **명령 프롬프트(cmd.exe)** 에서는 다음 명령을 사용할 수 있습니다(파일이 현재 폴더에 있는 경우).

```cmd
mysql -u root -p < hospital_db.sql
```

> 주의: 이 덤프에 `DROP TABLE IF EXISTS`가 포함되어 있으므로 기존 `hospital_db`가 있으면 데이터가 교체될 수 있습니다. 필요한 데이터는 먼저 백업하세요. PowerShell에서는 위와 같은 `<` 리디렉션이 버전에 따라 동작하지 않을 수 있으므로 **명령 프롬프트(cmd.exe)** 를 사용하세요.

복원 후 MySQL에서 데이터 확인:

```sql
USE hospital_db;
SHOW TABLES;
SELECT COUNT(*) FROM hospital;
SELECT COUNT(*) FROM hospital_dept;
SELECT COUNT(*) FROM department;
SELECT COUNT(*) FROM region;
```

테이블은 `hospital`, `hospital_dept`, `department`, `region` 네 개입니다. **병원과 지역의 JOIN 키는 `hospital.region_id = region.region_id`** 입니다. `region.sgg_code`는 있어도 `hospital.sgg_code`는 없으므로 예전 쿼리와 혼동하면 안 됩니다.

## 3. DB 접속 설정 (개인 컴퓨터마다 한 번)

`app/config_example.py`를 복사해 `app/config.py`로 이름을 바꾸고 자신의 MySQL 비밀번호를 지정합니다.

```python
DB = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "본인_mysql_비밀번호",
    "database": "hospital_db",
    "charset": "utf8mb4",
    "connect_timeout": 5,
    "read_timeout": 20,
    "write_timeout": 20,
}
```

비밀번호가 들어간 `config.py`는 **GitHub 업로드 및 제출에서 제외**합니다. 다른 컴퓨터에서는 `config_example.py`로부터 각자 생성합니다.

## 4. Python 프로그램 실행

프로젝트 최상위 폴더에서:

```bash
python app/main.py
```

0번을 누를 때까지 메뉴가 반복됩니다. 선택 조건은 Enter로 생략할 수 있고, 시도·시군구·종별·진료과목 입력에서 **`?`** 를 누르면 DB에 존재하는 값 목록을 보여줍니다.

**시도 이름은 실제 DB 값을 사용하세요.** 예를 들어 `서울`, `경기`, `부산`이며, `서울특별시`처럼 입력하면 일치하지 않을 수 있습니다. `?`로 정확한 값을 확인하세요.

1번과 2번, 4번, 7번은 결과가 많으면 각각 최대 50/100/30/100건만 보여줍니다. 표시 건수는 전국 전체 결과 건수가 아닐 수 있습니다. 5번 TOP N의 N은 1~100입니다.

## 5. 프로젝트 구조

```text
code3/
├── .gitignore
├── README.md
├── requirements.txt
├── app/
│   ├── main.py           # 메뉴, 입력, 결과 출력, 예외 처리
│   ├── queries.py        # 조회 함수 8개와 입력 도우미
│   └── config_example.py # 비밀번호 없는 설정 예시
├── sql/
│   └── README.md         # 데이터 파일 공유와 DB 스키마 설명
└── tests/
    └── test_queries.py  # DB 연결 없이 SQL 구조/파라미터 검증
```

실제 SQL 덤프는 별도로 받아 보관하고 데이터베이스에 복원합니다. 대용량 데이터 파일과 비밀번호는 공개 GitHub 저장소에 올리지 않습니다.

## 6. 테스트

```bash
python -m pip install pytest
python -m pytest -q
```

이 테스트는 함수가 올바른 JOIN 키와 안전한 파라미터를 만드는지 확인합니다. **MySQL 실제 실행 테스트를 대체하지는 않습니다.** 최종 제출 전 반드시 팀원의 MySQL에서 F1~F3 및 E1~E5를 실행하고 결과를 확인해야 합니다.

## 데이터와 결과 해석의 주의점

- 병원·전문의 수는 SQL 덤프 시점의 정적 공공데이터 기준이며 실시간 진료 가능 여부를 보장하지 않습니다.
- 8번 기능은 `region` 테이블에 존재하는 지역 중 해당 진료과목이 없는 지역을 반환합니다. 전국 모든 행정구역의 의료 공백을 의미하는 것은 아닙니다.
- `병원 찾기` 프로젝트 데이터 출처: 건강보험심사평가원 전국 병의원 및 약국 현황(공공데이터포털).