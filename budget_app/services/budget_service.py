# 이 파일은 월별 예산 저장과 조회 업무만 담당한다.

from typing import Optional  # 설정되지 않은 예산을 None으로 표시하기 위해 가져온다.

from budget_app.repositories import BudgetStore  # 월별 예산 파일 저장소를 가져온다.


class MonthlyBudgetService:  # 월별 예산 저장소를 서비스 계층에서 사용할 수 있게 연결한다.
    def __init__(self, budgets: BudgetStore) -> None:  # 예산 저장소를 받는다.
        self._budgets = budgets  # 예산 저장소를 내부 전용 변수에 보관한다.

    def set(self, month: str, amount: object) -> int:  # 월 예산을 새로 저장하거나 기존 값을 수정한다.
        return self._budgets.set(month, amount)  # 예산 저장소에 검증과 저장을 맡기고 실제 금액을 돌려준다.

    def get(self, month: str) -> Optional[int]:  # 특정 월의 예산을 조회한다.
        return self._budgets.get(month)  # 예산 저장소에서 금액을 찾아서 돌려준다.
