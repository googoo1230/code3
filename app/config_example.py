"""이 파일을 config.py로 복사하고 본인 MySQL 접속 정보를 입력하세요.

config.py는 .gitignore에 포함되어 있으므로 GitHub에 올리지 마세요.
"""

DB = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "",  # 자신의 MySQL 비밀번호 (공유/제출 금지)
    "database": "hospital_db",
    "charset": "utf8mb4",
    "connect_timeout": 5,
    "read_timeout": 20,
    "write_timeout": 20,
}