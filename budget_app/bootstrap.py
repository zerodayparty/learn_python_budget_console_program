# 이 파일은 저장소와 서비스를 한 번만 조립하는 프로그램 구성 시작점을 담당한다.

from pathlib import Path  # Path는 사용자가 선택한 데이터 저장 폴더를 다루게 해 준다.

from budget_app.repositories import BudgetStore, CategoryStore, TransactionRepository  # 조립할 세 저장소 클래스를 가져온다.
from budget_app.services import BudgetService  # 세부 서비스를 묶는 조립 서비스를 가져온다.


def build_service(data_dir: Path) -> BudgetService:  # 지정된 데이터 폴더를 사용하는 전체 서비스를 만든다.
    transactions = TransactionRepository(data_dir)  # 거래 파일 저장소를 준비한다.
    categories = CategoryStore(data_dir)  # 카테고리 파일 저장소를 준비한다.
    budgets = BudgetStore(data_dir)  # 예산 파일 저장소를 준비한다.
    return BudgetService(transactions, categories, budgets)  # 세 저장소가 연결된 조립 서비스를 돌려준다.
