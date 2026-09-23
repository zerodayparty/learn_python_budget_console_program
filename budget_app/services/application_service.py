# 이 파일은 분리된 세부 서비스를 기존 BudgetService 인터페이스로 묶어 제공한다.

from pathlib import Path  # Path는 CSV 파일 경로 타입을 표시하기 위해 가져온다.
from typing import Iterator, List, Optional, Tuple  # 기존 공개 메서드의 입력과 반환 타입을 표시한다.

from budget_app.dtos import CreateTransactionDTO, SearchTransactionsDTO, UpdateTransactionDTO  # 거래 서비스에 전달할 DTO들을 가져온다.
from budget_app.models import MonthlySummary, Transaction  # 기존 공개 메서드의 거래와 요약 반환 타입을 가져온다.
from budget_app.repositories import BudgetStore, CategoryStore, TransactionRepository  # 세부 서비스를 조립할 저장소들을 가져온다.
from budget_app.services.budget_service import MonthlyBudgetService  # 월별 예산 서비스를 가져온다.
from budget_app.services.category_service import CategoryService  # 카테고리 서비스를 가져온다.
from budget_app.services.csv_service import CsvService  # CSV 서비스를 가져온다.
from budget_app.services.summary_service import SummaryService  # 월별 요약 서비스를 가져온다.
from budget_app.services.transaction_service import TransactionService  # 거래 서비스를 가져온다.


class BudgetService:  # 기존 CLI 호출을 유지하면서 세부 서비스에 작업을 전달하는 조립 서비스다.
    def __init__(self, transactions: TransactionRepository, categories: CategoryStore, budgets: BudgetStore) -> None:  # 세 저장소를 받아 모든 세부 서비스를 조립한다.
        self._transaction_service = TransactionService(transactions, categories)  # 거래 서비스에 필요한 저장소를 연결한다.
        self._summary_service = SummaryService(transactions, budgets)  # 요약 서비스에 필요한 저장소를 연결한다.
        self._budget_service = MonthlyBudgetService(budgets)  # 예산 서비스에 예산 저장소를 연결한다.
        self._category_service = CategoryService(categories, transactions)  # 카테고리 서비스에 필요한 저장소를 연결한다.
        self._csv_service = CsvService(transactions, self._transaction_service)  # CSV 서비스에 거래 저장소와 거래 서비스를 연결한다.

    def add_transaction(self, request: CreateTransactionDTO) -> Transaction:  # 거래 추가 요청을 거래 서비스에 전달한다.
        return self._transaction_service.add(request)  # 저장된 거래를 호출한 쪽에 돌려준다.

    def list_transactions(self, limit: int) -> Iterator[Transaction]:  # 거래 목록 요청을 거래 서비스에 전달한다.
        return self._transaction_service.list(limit)  # 최신순 거래 제너레이터를 돌려준다.

    def search_transactions(self, criteria: SearchTransactionsDTO) -> Iterator[Transaction]:  # 거래 검색 요청을 거래 서비스에 전달한다.
        return self._transaction_service.search(criteria)  # 조건에 맞는 거래 제너레이터를 돌려준다.

    def get_transaction(self, transaction_id: str) -> Optional[Transaction]:  # 거래 한 건 조회 요청을 거래 서비스에 전달한다.
        return self._transaction_service.get(transaction_id)  # 찾은 거래를 돌려주고 없으면 None을 돌려준다.

    def update_transaction(self, request: UpdateTransactionDTO) -> Transaction:  # 거래 수정 요청을 거래 서비스에 전달한다.
        return self._transaction_service.update(request)  # 수정된 거래를 돌려준다.

    def delete_transaction(self, transaction_id: str) -> None:  # 거래 삭제 요청을 거래 서비스에 전달한다.
        self._transaction_service.delete(transaction_id)  # 거래 서비스에 삭제 작업을 맡긴다.

    def monthly_summary(self, month: str, top: int) -> MonthlySummary:  # 월별 요약 요청을 요약 서비스에 전달한다.
        return self._summary_service.monthly(month, top)  # 계산된 월별 요약을 돌려준다.

    def set_budget(self, month: str, amount: object) -> int:  # 예산 저장 요청을 월별 예산 서비스에 전달한다.
        return self._budget_service.set(month, amount)  # 실제 저장한 예산 금액을 돌려준다.

    def get_budget(self, month: str) -> Optional[int]:  # 예산 조회 요청을 월별 예산 서비스에 전달한다.
        return self._budget_service.get(month)  # 저장된 예산을 돌려주고 없으면 None을 돌려준다.

    def add_category(self, name: str) -> str:  # 카테고리 추가 요청을 카테고리 서비스에 전달한다.
        return self._category_service.add(name)  # 실제 저장한 카테고리 이름을 돌려준다.

    def list_categories(self) -> List[str]:  # 카테고리 목록 요청을 카테고리 서비스에 전달한다.
        return self._category_service.list()  # 정렬된 카테고리 목록을 돌려준다.

    def category_exists(self, name: str) -> bool:  # 카테고리 존재 확인 요청을 카테고리 서비스에 전달한다.
        return self._category_service.exists(name)  # 등록 여부를 참 또는 거짓으로 돌려준다.

    def remove_category(self, name: str) -> None:  # 카테고리 삭제 요청을 카테고리 서비스에 전달한다.
        self._category_service.remove(name)  # 카테고리 서비스에 삭제 작업을 맡긴다.

    def import_csv(self, source: Path) -> Tuple[int, int, List[str]]:  # CSV 가져오기 요청을 CSV 서비스에 전달한다.
        return self._csv_service.import_file(source)  # 저장 수, 건너뜀 수, 오류 목록을 돌려준다.

    def export_csv(self, output: Path, month: Optional[str] = None, date_from: Optional[str] = None, date_to: Optional[str] = None) -> int:  # CSV 내보내기 요청을 CSV 서비스에 전달한다.
        return self._csv_service.export_file(output, month, date_from, date_to)  # 실제 내보낸 거래 개수를 돌려준다.
