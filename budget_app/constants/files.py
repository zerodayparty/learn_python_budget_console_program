# 이 파일은 가계부 저장소 폴더, 파일 이름, CSV 열 구조에 대한 기준 상수를 모아둔다.


DEFAULT_DATA_DIR = "data"  # 가계부 데이터를 저장할 기본 폴더 이름이다.
TRANSACTIONS_FILENAME = "transactions.jsonl"  # 거래 내역을 저장할 기본 파일 이름이다.
CATEGORIES_FILENAME = "categories.jsonl"  # 카테고리 목록을 저장할 기본 파일 이름이다.
BUDGETS_FILENAME = "budgets.jsonl"  # 월별 예산을 저장할 기본 파일 이름이다.

CSV_COLUMNS = ["date", "type", "category", "amount", "memo", "tags"]  # CSV 파일의 열(Column) 순서다.
CSV_REQUIRED_COLUMNS = {"date", "type", "category", "amount"}  # CSV 가져오기 시 반드시 들어있어야 하는 필수 열 목록이다.
