# 이 파일은 월별 수입, 지출, 카테고리 합계와 예산 요약 계산만 담당한다.

from typing import Dict, Tuple  # 카테고리 합계 사전과 정렬 기준 튜플 타입을 표시한다.

from budget_app.constants import ErrorMessages  # 요약 개수 오류 메시지를 가져온다.
from budget_app.exceptions import ValidationError  # 잘못된 요약 요청을 알리기 위해 가져온다.
from budget_app.models import MonthlySummary  # 월별 요약 결과 모델을 가져온다.
from budget_app.repositories import BudgetStore, TransactionRepository  # 거래와 예산 저장소를 가져온다.
from budget_app.validators import validate_month  # 요약할 월 검증 함수를 가져온다.


def _category_expense_sort_key(item: Tuple[str, int]) -> Tuple[int, str]:  # 카테고리 지출을 정렬할 기준을 만든다.
    category = item[0]  # 첫 번째 값인 카테고리 이름을 꺼낸다.
    amount = item[1]  # 두 번째 값인 카테고리 지출 합계를 꺼낸다.
    return -amount, category  # 금액은 큰 순서, 같은 금액은 이름 순서가 되도록 기준을 돌려준다.


class SummaryService:  # 월별 거래 통계와 예산 사용 결과 계산을 담당한다.
    def __init__(self, transactions: TransactionRepository, budgets: BudgetStore) -> None:  # 거래와 예산 저장소를 받는다.
        self._transactions = transactions  # 거래 저장소를 내부 전용 변수에 보관한다.
        self._budgets = budgets  # 예산 저장소를 내부 전용 변수에 보관한다.

    def monthly(self, month: str, top: int) -> MonthlySummary:  # 한 달의 수입, 지출, 카테고리 합계, 예산을 계산한다.
        checked_month = validate_month(month)  # 계산할 월을 YYYY-MM 형식으로 검사한다.
        if top <= 0:  # 상위 카테고리 개수가 0 또는 음수인지 확인한다.
            raise ValidationError(*ErrorMessages.TOP_MUST_BE_POSITIVE)  # 양수 TOP 개수 오류를 알린다.
        total_income = 0  # 총수입 계산을 0에서 시작한다.
        total_expense = 0  # 총지출 계산을 0에서 시작한다.
        transaction_count = 0  # 대상 월의 거래 개수 계산을 0에서 시작한다.
        category_totals: Dict[str, int] = {}  # 지출 카테고리별 합계를 담을 빈 사전을 만든다.
        for transaction in self._transactions.iter_latest():  # 거래 파일을 최신순으로 한 건씩 읽는다.
            if not transaction.date.startswith(checked_month + "-"):  # 거래가 계산 대상 월에 속하는지 확인한다.
                continue  # 다른 월의 거래는 건너뛴다.
            transaction_count += 1  # 대상 월의 거래 개수에 1을 더한다.
            if transaction.type == "income":  # 현재 거래가 수입인지 확인한다.
                total_income += transaction.amount  # 수입 금액을 총수입에 더한다.
            else:  # 검증된 거래 타입이 지출인 경우다.
                total_expense += transaction.amount  # 지출 금액을 총지출에 더한다.
                category_totals[transaction.category] = category_totals.get(transaction.category, 0) + transaction.amount  # 현재 카테고리의 지출 합계를 갱신한다.
        sorted_categories = list(category_totals.items())  # 카테고리와 합계 쌍을 정렬 가능한 목록으로 만든다.
        sorted_categories.sort(key=_category_expense_sort_key)  # 금액 큰 순서와 이름 순서 기준으로 정렬한다.
        return MonthlySummary(  # 계산한 모든 값을 월별 요약 모델로 묶어 돌려준다.
            month=checked_month,  # 검사한 계산 대상 월을 저장한다.
            total_income=total_income,  # 계산한 총수입을 저장한다.
            total_expense=total_expense,  # 계산한 총지출을 저장한다.
            category_expenses=sorted_categories[:top],  # 정렬된 카테고리 중 요청한 개수만 저장한다.
            budget=self._budgets.get(checked_month),  # 저장된 월 예산을 찾아서 저장한다.
            transaction_count=transaction_count,  # 계산한 거래 개수를 저장한다.
        )  # 월별 요약 모델 만들기를 끝낸다.
