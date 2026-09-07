# 이 파일은 허용된 거래 유형과 프로그램 시작 시 등록될 기본 카테고리 목록 상수를 모아둔다.


TRANSACTION_TYPES = ("income", "expense")  # 거래 유형으로 허용되는 수입(income)과 지출(expense) 목록이다.
ALLOWED_TYPES = set(TRANSACTION_TYPES)  # 빠른 포함 여부 검사를 위해 집합(set) 자료형으로 보관한다.

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
