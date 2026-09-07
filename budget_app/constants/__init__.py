# 이 파일은 constants 패키지의 모든 세부 상수를 한곳으로 모아 외부에 제공(re-export)한다.

from budget_app.constants.categories import (  # 카테고리 및 거래 타입 관련 상수를 가져온다.
    ALLOWED_TYPES,  # 허용된 거래 타입 집합이다.
    DEFAULT_CATEGORIES,  # 기본 카테고리 묶음이다.
    TRANSACTION_TYPES,  # 허용된 거래 타입 튜플이다.
)  # 카테고리 상수 가져오기를 마친다.
from budget_app.constants.view_limits import (  # 화면 출력 개수 제한 관련 상수를 가져온다.
    DEFAULT_LIST_LIMIT,  # 거래 목록 기본 조회 개수다.
    DEFAULT_SUMMARY_TOP,  # 월별 요약 기본 상위 개수다.
)  # 화면 제한 상수 가져오기를 마친다.
from budget_app.constants.datetime import (  # 날짜 및 시간 관련 상수를 가져온다.
    DATE_FORMAT,  # 날짜 표준 포맷 문자열이다.
    DATE_PATTERN,  # 날짜 검사용 정규식 패턴이다.
    MONTH_FORMAT,  # 월 표준 포맷 문자열이다.
    MONTH_PATTERN,  # 월 검사용 정규식 패턴이다.
)  # 날짜 상수 가져오기를 마친다.
from budget_app.constants.error_messages import ErrorMessages  # 오류 원인 및 힌트 모음 클래스를 가져온다.
from budget_app.constants.repository_files import (  # 저장소 파일 및 CSV 관련 상수를 가져온다.
    BUDGETS_FILENAME,  # 예산 저장 파일 이름이다.
    CATEGORIES_FILENAME,  # 카테고리 저장 파일 이름이다.
    CSV_COLUMNS,  # CSV 열 순서 목록이다.
    CSV_REQUIRED_COLUMNS,  # CSV 필수 열 집합이다.
    DEFAULT_DATA_DIR,  # 기본 데이터 저장 폴더 이름이다.
    TRANSACTIONS_FILENAME,  # 거래 저장 파일 이름이다.
)  # 파일 상수 가져오기를 마친다.


__all__ = [  # 이 패키지 외부로 공개할 상수 및 클래스 이름 목록이다.
    "ALLOWED_TYPES",  # 허용된 거래 타입 집합을 공개한다.
    "DEFAULT_CATEGORIES",  # 기본 카테고리 목록을 공개한다.
    "TRANSACTION_TYPES",  # 허용된 거래 타입 튜플을 공개한다.
    "DEFAULT_LIST_LIMIT",  # 기본 조회 개수를 공개한다.
    "DEFAULT_SUMMARY_TOP",  # 기본 요약 상위 개수를 공개한다.
    "DATE_FORMAT",  # 날짜 표준 포맷을 공개한다.
    "DATE_PATTERN",  # 날짜 정규식을 공개한다.
    "MONTH_FORMAT",  # 월 표준 포맷을 공개한다.
    "MONTH_PATTERN",  # 월 정규식을 공개한다.
    "ErrorMessages",  # 에러 메시지 클래스를 공개한다.
    "BUDGETS_FILENAME",  # 예산 파일명을 공개한다.
    "CATEGORIES_FILENAME",  # 카테고리 파일명을 공개한다.
    "CSV_COLUMNS",  # CSV 열 목록을 공개한다.
    "CSV_REQUIRED_COLUMNS",  # CSV 필수 열을 공개한다.
    "DEFAULT_DATA_DIR",  # 기본 데이터 폴더명을 공개한다.
    "TRANSACTIONS_FILENAME",  # 거래 파일명을 공개한다.
]  # 공개 목록 작성을 마친다.
