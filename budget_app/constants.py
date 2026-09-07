# 이 파일은 프로그램 전체에서 변하지 않고 반복해서 사용하는 고정값(상수)을 모아둔다.

import re  # 문자열의 모양(패턴)을 정규식으로 검사하기 위해 re 도구를 가져온다.


# 1. 날짜 및 시간 관련 상수
DATE_FORMAT = "%Y-%m-%d"  # 연-월-일 날짜를 다룰 때 사용할 표준 포맷 문자열이다.
MONTH_FORMAT = "%Y-%m"  # 연-월을 다룰 때 사용할 표준 포맷 문자열이다.
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")  # 날짜가 숫자로 4자리-2자리-2자리인지 검사하는 정규식 규칙이다.
MONTH_PATTERN = re.compile(r"^\d{4}-\d{2}$")  # 월이 숫자로 4자리-2자리인지 검사하는 정규식 규칙이다.


# 2. 거래 타입 관련 상수
TRANSACTION_TYPES = ("income", "expense")  # 거래 유형으로 허용되는 수입(income)과 지출(expense) 목록이다.
ALLOWED_TYPES = set(TRANSACTION_TYPES)  # 빠른 포함 여부 검사를 위해 집합(set) 자료형으로 보관한다.


# 3. 기본 데이터 파일 및 카테고리 상수
DEFAULT_DATA_DIR = "data"  # 가계부 데이터를 저장할 기본 폴더 이름이다.
TRANSACTIONS_FILENAME = "transactions.jsonl"  # 거래 내역을 저장할 기본 파일 이름이다.
CATEGORIES_FILENAME = "categories.jsonl"  # 카테고리 목록을 저장할 기본 파일 이름이다.
BUDGETS_FILENAME = "budgets.jsonl"  # 월별 예산을 저장할 기본 파일 이름이다.
DEFAULT_CATEGORIES = (  # 프로그램 최초 실행 시 자동으로 생성해 줄 기본 카테고리 8가지다.
    "food",  # 식비 카테고리다.
    "transport",  # 교통비 카테고리다.
    "rent",  # 주거비/월세 카테고리다.
    "salary",  # 급여/수입 카테고리다.
    "utilities",  # 공과금 카테고리다.
    "health",  # 의료/건강 카테고리다.
    "leisure",  # 여가/문화 카테고리다.
    "other",  # 기타 카테고리다.
)  # 기본 카테고리 묶음을 마친다.


# 4. CSV 파일 입출력(Import/Export) 관련 상수
CSV_COLUMNS = ["date", "type", "category", "amount", "memo", "tags"]  # CSV 파일의 열(Column) 순서다.
CSV_REQUIRED_COLUMNS = {"date", "type", "category", "amount"}  # CSV 가져오기 시 반드시 들어있어야 하는 필수 열 목록이다.


# 5. CLI(명령줄) 및 화면 출력 기본값 상수
DEFAULT_LIST_LIMIT = 10  # 거래 목록 조회 시 기본으로 화면에 보여줄 개수다.
DEFAULT_SUMMARY_TOP = 3  # 월별 요약 시 가장 지출이 큰 상위 카테고리 기본 출력 개수다.
