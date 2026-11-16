# 병원·진료과목 찾기 | 6조

MySQL의 병원 데이터를 Python으로 검색·집계하는 콘솔 프로그램입니다. **처음 실행한다면 아래 1~5단계를 순서대로 진행하세요.**

## 프로그램 구조

**사용자가 검색 조건을 입력하면 Python이 MySQL에서 병원 정보를 조회하고, 결과를 터미널에 표로 보여주는 메뉴형 프로그램**입니다. 웹사이트가 아닌 콘솔 프로그램이며, 종료를 선택할 때까지 메뉴를 반복해서 사용할 수 있습니다.

```text
사용자 (메뉴 1~8 선택, 지역·진료과목 등 입력)
    ↓
app/main.py       입력 확인 · 메뉴 처리 · 결과 출력
    ↓
app/queries.py    조건에 맞는 SQL 실행 (JOIN · 집계 · 정렬)
    ↓
MySQL hospital_db 병원 · 지역 · 진료과목 데이터 조회
    ↓
검색 결과를 터미널에 표시
```

데이터는 **병원(`hospital`)**, **지역(`region`)**, **진료과목(`department`)**, **병원별 진료과목(`hospital_dept`)** 4개 테이블로 구성됩니다. 메뉴 **1~3번은 기본 검색·현황**, **4~8번은 상세 조회·순위·통계 등 추가 기능**입니다.

## 터미널 실행 화면 예시

프로그램을 실행하면 아래처럼 **1~8번 메뉴가 먼저 표시**됩니다. 번호를 입력하면 검색 조건을 묻고, 조회 결과를 표로 출력한 뒤 다시 메뉴로 돌아옵니다.

```text
========== 병원 찾기 ==========
 1. 병원 검색
 2. 진료과목으로 병원 찾기
 3. 지역별 진료과목 현황
 4. 병원 상세 (진료과목 목록)
 5. 전문의가 많은 병원 TOP N
 6. 종별 병원 수 통계
 7. 진료과목이 많은 병원
 8. 특정 과목 병원이 없는 지역
 0. 종료
===============================
메뉴 선택: 1

[병원 검색]
  시도 (예: 서울) [생략: Enter] [목록: ?]: 서울
  시군구 (예: 강남구) [생략: Enter] [목록: ?]: 강남구
  종별 (예: 의원) [생략: Enter] [목록: ?]: 의원
  병원명 일부 [생략: Enter]:

[조건에 맞는 병원 검색 결과 표가 출력됩니다]
표시된 결과: (조회된 건수)건 (최대 50건까지 출력)

(Enter를 누르면 메뉴로 돌아갑니다)
```

> 위 화면은 **입력 흐름을 보여주는 예시**입니다. 실제 병원 목록과 결과 건수는 데이터 및 입력 조건에 따라 달라집니다. `[생략: Enter]`는 입력 없이 넘어갈 수 있다는 뜻이고, `[목록: ?]`는 `?`를 입력해 선택 가능한 값을 볼 수 있다는 뜻입니다.

## 준비물

- MySQL Server 및 **MySQL Workbench**
- **IntelliJ IDEA** + Python 플러그인, Python 설치
- 별도로 전달받은 **`hospital_db.sql`** (GitHub에 포함되지 않음)

## 1. MySQL Workbench에서 SQL 복원

1. MySQL Workbench 실행 → `Local instance MySQL80` 등 본인 MySQL 연결 열기
2. 상단 **Server → Data Import** 선택
3. **Import from Self-Contained File** 선택 → `hospital_db.sql` 지정
4. **Start Import** 클릭 → 완료 후 왼쪽 **SCHEMAS 새로고침**

> SQL 파일에 데이터베이스 생성 구문과 데이터가 포함되어 있어 별도 CSV는 필요하지 않습니다. **주의:** 덤프에는 `DROP TABLE IF EXISTS`가 있어 기존 데이터가 교체될 수 있습니다. 기존 DB가 있다면 백업 후 진행하세요.

### 복원 확인

SQL 편집기에서 다음을 실행합니다(상단 번개 버튼).

```sql
SHOW DATABASES;
USE hospital_db;
SHOW TABLES;
SELECT COUNT(*) AS hospital_count FROM hospital;
SELECT name, type, address, tel FROM hospital LIMIT 10;
```

**정상 기준:** `hospital_db`가 존재하고, `hospital` · `region` · `department` · `hospital_dept` **4개 테이블**이 보이며, 병원 수가 **0보다 크고** 병원 정보가 출력됩니다. 테이블 표시 순서는 상관없습니다.

## 2. IntelliJ IDEA에서 프로젝트 열기

1. 이 저장소 오른쪽 위 **Code → Download ZIP** → 압축 해제
2. IntelliJ IDEA → **Open** → 압축 해제한 **프로젝트 폴더** 선택
3. **File → Settings → Plugins → Marketplace**에서 JetBrains **Python** 플러그인 설치 및 재시작 (설치가 안 되면 호환되는 Python Community Edition 플러그인 확인)
4. **File → Project Structure → SDKs**에서 Python 인터프리터 추가. 가능하면 프로젝트용 **Virtualenv (`.venv`)** 생성

> **폴더 확인:** IntelliJ 프로젝트 창에서 `app`, `tests`, `requirements.txt`가 같은 폴더 바로 아래에 있어야 합니다. `code3-main/code3-main/`처럼 한 단계 더 중첩되었다면, **안쪽 폴더**가 실제 프로젝트 루트입니다.

## 3. MySQL 연결 정보 설정

`app/config_example.py`를 복사해 **`app/config.py`**로 저장하고, 아래 항목을 본인 환경에 맞게 수정합니다. 나머지 설정은 그대로 두세요.

```python
DB = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "본인_MySQL_비밀번호",
    "database": "hospital_db",
    "charset": "utf8mb4",
    "connect_timeout": 5,
    "read_timeout": 20,
    "write_timeout": 20,
}
```

**`config.py`에는 비밀번호가 있으므로 GitHub에 업로드하지 마세요.**

## 4. 라이브러리 설치 및 프로그램 실행

IntelliJ 하단 **Terminal**을 열고, `requirements.txt`가 있는 **프로젝트 루트**에서 실행합니다.

```powershell
python -m pip install -r requirements.txt
python app/main.py
```

Python 인터프리터를 `.venv`에 만들었다면 Windows에서는 다음처럼 직접 실행해도 됩니다.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app\main.py
```

**폴더가 중첩되어 있고 `.venv`는 바깥 폴더에 있는 경우** (현재 작업 환경: 터미널 위치가 바깥 `code3-main`일 때):

```powershell
.\.venv\Scripts\python.exe -m pip install -r .\code3-main\requirements.txt
.\.venv\Scripts\python.exe .\code3-main\app\main.py
```

예를 들어 터미널이 `C:\Users\feas0\OneDrive\바탕 화면\code3-main>` 위치라면 위 중첩 폴더용 명령어를 사용하세요. **현재 작업 환경에서 실제로 실행되는 명령어**는 `.\.venv\Scripts\python.exe .\code3-main\app\main.py`입니다.

Python 버전 확인은 같은 위치에서 `.\.venv\Scripts\python.exe --version`을 실행하면 됩니다.

성공하면 `========== 병원 찾기 ==========` 메뉴가 나타납니다. **0**은 종료, 선택 입력은 **Enter**로 생략, 지역·종별·과목의 **?**는 사용 가능한 값 목록을 표시합니다.

## 5. 메뉴별 실행 테스트

메뉴 번호를 입력하고, 화면에 나타나는 질문 순서대로 아래 값을 입력하세요. **‘생략’은 Enter만 누르면 됩니다.** 실제 DB 값에 맞춰 `서울`처럼 입력합니다(정확한 값은 `?`로 확인).

| 메뉴 | 테스트 입력 (프로그램 질문 순서) | 정상 확인 기준 |
|---|---|---|
| **1. 병원 검색** | 시도 `서울` → 시군구 `강남구` → 종별 `의원` → 병원명 생략 | 조건에 맞는 병원명·주소·전화 출력 |
| **2. 진료과목으로 병원 찾기** | 진료과목 `내과` → 시도 `서울` → 시군구 `강남구` | 병원 목록과 전문의 수 출력 |
| **3. 지역별 진료과목 현황** | 시도 `서울` → 진료과목 `내과` | 시군구별 병원 수·전문의 합계 |
| **4. 병원 상세** | 병원명 일부 `삼성서울병원` | 주소 및 진료과목 목록 출력 |
| **5. 전문의 많은 병원 TOP N** | 진료과목 `내과` → 시도 `서울` → N `5` | 최대 5개, 전문의 수 내림차순 |
| **6. 종별 병원 수 통계** | 시도 `서울` | 종별(의원·병원 등) 병원 수 |
| **7. 진료과목이 많은 병원** | 시군구 `강남구` → 최소 과목 수 `5` → 시도 `서울` | 과목 수 5개 이상 병원 출력 |
| **8. 특정 과목 병원이 없는 지역** | 시도 `서울` → 진료과목 `핵의학과` | 해당 과목 병원이 없는 시군구 출력 |

**추가 확인:** 결과가 나오면 Enter를 눌러 메인 메뉴로 복귀하는지 확인하세요. 5번에서 N에 `0`이나 `101`을 입력하면 다시 입력하도록 안내해야 합니다. 8번은 조건에 따라 결과가 **0건이어도 정상**일 수 있습니다.

> **출력 참고:** 1번·4번은 긴 주소나 진료과목 때문에 일부 터미널 환경에서 표 테두리가 어긋날 수 있습니다. 데이터 조회 오류와는 별개이며, 터미널 창을 넓혀 확인하세요.

## 자주 발생하는 오류

| 증상 | 확인할 것 |
|---|---|
| `requirements.txt` 파일을 찾을 수 없음 | 터미널 위치 확인. 프로젝트 폴더가 한 번 더 중첩되어 있는지 확인 |
| `*.py` 지원 플러그인 알림 | IntelliJ Python 플러그인 설치·활성화 |
| `app/config.py`가 없음 | `config_example.py`를 복사해 `config.py` 생성 |
| `MySQL 연결 오류` | MySQL 서버 실행 여부, `config.py`의 계정·비밀번호·포트 확인 |
| 결과가 0건 | 입력값 확인. `?`로 DB에 저장된 정확한 지역·과목명 조회 |

## 기능 및 파일 구성

- **기본 기능(1~3):** 병원 검색, 진료과목별 검색, 지역별 현황
- **추가 기능(4~8):** 상세 정보, 전문의 TOP N, 종별 통계, 다과목 병원, 특정 과목이 없는 지역
- `app/main.py`: 메뉴·입력·표 출력 / `app/queries.py`: SQL 조회 / `tests/`: 자동 테스트

자동 테스트는 프로젝트 루트에서 다음 명령으로 실행합니다. **자동 테스트는 실제 MySQL 조회 테스트를 대체하지 않습니다.**

```powershell
python -m pip install pytest
python -m pytest -q
```
