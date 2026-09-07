# 이 파일은 저장소 기능을 조합해서 가계부의 실제 업무 규칙을 처리한다.

import csv  # csv는 Comma-Separated Values(쉼표로 구분한 값) 파일을 읽고 쓰는 도구다.
import uuid  # uuid는 Universally Unique Identifier(범용 고유 식별자)를 만드는 도구다.
from pathlib import Path  # Path는 파일 경로를 안전하게 조합하고 다루는 도구다.
from typing import Dict, Iterator, List, Optional, Tuple  # 함수가 주고받는 값의 자료형을 표시한다.

from budget_app.exceptions import BudgetAppError, ConflictError, NotFoundError, ValidationError  # 업무 규칙 위반을 설명할 오류들이다.
from budget_app.models import MonthlySummary, Transaction  # 업무에서 사용할 거래와 요약 데이터 모양이다.
from budget_app.repositories import BudgetStore, CategoryStore, TransactionRepository  # 세 JSONL 파일을 담당하는 저장소들이다.
from budget_app.validators import (  # 입력값을 종류별로 검사하는 함수들을 가져온다.
    normalize_tags,  # 쉼표로 입력한 태그를 목록으로 정리한다.
    validate_amount,  # 금액이 0보다 큰 정수인지 검사한다.
    validate_category_name,  # 카테고리 이름이 저장 가능한지 검사한다.
    validate_date,  # 날짜가 YYYY-MM-DD 형식의 실제 날짜인지 검사한다.
    validate_month,  # 월이 YYYY-MM 형식의 실제 월인지 검사한다.
    validate_transaction_type,  # 거래 타입이 income 또는 expense인지 검사한다.
)  # 입력값 검사 함수 가져오기를 끝낸다.
from budget_app.constants import (  # 공통 상수 모듈에서 CSV 열 규칙과 에러 메시지를 가져온다.
    CSV_COLUMNS,  # CSV 내보내기/가져오기 열 순서다.
    CSV_REQUIRED_COLUMNS,  # CSV 필수 열 목록이다.
    ErrorMessages,  # 오류 원인 및 해결 힌트 모음 클래스를 가져온다.
)  # CSV 및 메시지 상수 가져오기를 끝낸다.


def _category_expense_sort_key(item: Tuple[str, int]) -> Tuple[int, str]:  # 카테고리 지출을 정렬할 기준을 만든다.
    category = item[0]  # 첫 번째 값인 카테고리 이름을 꺼낸다.
    amount = item[1]  # 두 번째 값인 카테고리 지출 합계를 꺼낸다.
    return -amount, category  # 금액은 큰 순서, 같은 금액은 이름 순서가 되도록 기준을 돌려준다.


class BudgetService:  # 여러 저장소를 연결해 가계부 규칙을 실행하는 서비스 클래스다.
    def __init__(  # 서비스가 사용할 세 저장소를 외부에서 받는다.
        self,  # 현재 생성되는 서비스 객체 자신을 뜻한다.
        transactions: TransactionRepository,  # 거래 파일을 담당하는 저장소다.
        categories: CategoryStore,  # 카테고리 파일을 담당하는 저장소다.
        budgets: BudgetStore,  # 예산 파일을 담당하는 저장소다.
    ) -> None:  # 객체를 준비만 하므로 돌려주는 값은 없다.
        self.transactions = transactions  # 거래 저장소를 서비스 안에 보관한다.
        self.categories = categories  # 카테고리 저장소를 서비스 안에 보관한다.
        self.budgets = budgets  # 예산 저장소를 서비스 안에 보관한다.

    def _new_id(self) -> str:  # 다른 거래와 겹칠 가능성이 매우 낮은 새 id를 만든다.
        while True:  # 저장된 거래와 겹치지 않는 id가 만들어질 때까지 반복한다.
            candidate = f"TX-{uuid.uuid4().hex[:12].upper()}"  # UUID 앞 12자에 TX 접두사를 붙여 읽기 쉬운 후보를 만든다.
            if self.transactions.find_by_id(candidate) is None:  # 후보 id가 기존 거래 파일에 없는지 확인한다.
                return candidate  # 실제로 겹치지 않는 후보만 새 거래 id로 돌려준다.

    def _checked_category(self, category: str) -> str:  # 카테고리 이름과 등록 여부를 함께 검사한다.
        cleaned = validate_category_name(category)  # 이름이 비어 있거나 너무 길지 않은지 검사한다.
        if not self.categories.exists(cleaned):  # 검사한 이름이 카테고리 파일에 등록되어 있는지 확인한다.
            raise ValidationError(*ErrorMessages.unregistered_category(cleaned))  # 등록되지 않은 카테고리 오류를 발생시킨다.
        return cleaned  # 검사와 등록 확인을 끝낸 이름을 돌려준다.

    def add_transaction(  # 사용자 입력으로 거래 한 건을 검사하고 저장한다.
        self,  # 현재 서비스 객체 자신을 뜻한다.
        date: str,  # YYYY-MM-DD 형식으로 받을 거래 날짜다.
        transaction_type: str,  # income 또는 expense로 받을 거래 타입이다.
        category: str,  # 등록된 이름으로 받을 카테고리다.
        amount: object,  # 0보다 큰 정수로 바꿀 수 있는 금액이다.
        memo: str = "",  # 선택 입력 메모이며 기본값은 빈 문자열이다.
        tags: Optional[object] = None,  # 선택 입력 태그 목록 또는 쉼표 문자열이다.
    ) -> Transaction:  # 검사와 저장을 끝낸 거래 객체를 돌려준다.
        checked_date = validate_date(date)  # 거래 날짜가 실제 달력에 존재하는지 검사한다.
        checked_type = validate_transaction_type(transaction_type)  # 수입 또는 지출인지 검사한다.
        checked_category = self._checked_category(category)  # 카테고리가 등록되어 있는지 검사한다.
        checked_amount = validate_amount(amount)  # 금액이 0보다 큰 정수인지 검사한다.
        normalized_memo = memo.strip()  # 메모 앞뒤의 불필요한 공백을 제거한다.
        normalized_tags = normalize_tags(tags)  # 태그를 중복 없는 문자열 목록으로 정리한다.
        transaction = Transaction(  # 검사를 통과한 값으로 새 거래 객체를 만든다.
            id=self._new_id(),  # 겹치지 않는 새 거래 id를 발급한다.
            date=checked_date,  # 검증된 날짜를 저장한다.
            type=checked_type,  # 검증된 거래 타입을 저장한다.
            category=checked_category,  # 검증된 카테고리를 저장한다.
            amount=checked_amount,  # 검증된 금액을 저장한다.
            memo=normalized_memo,  # 정리된 메모를 저장한다.
            tags=normalized_tags,  # 정리된 태그 목록을 저장한다.
        )  # 거래 객체 만들기를 끝낸다.
        self.transactions.append(transaction)  # 검사에 성공한 거래를 transactions.jsonl 마지막에 추가한다.
        return transaction  # 화면 출력이나 테스트에 쓸 수 있도록 저장한 거래를 돌려준다.

    def list_transactions(self, limit: int) -> Iterator[Transaction]:  # 최신 거래를 요청한 개수만큼 한 건씩 전달한다.
        if limit <= 0:  # 제한 개수가 0 또는 음수인지 검사한다.
            raise ValidationError(*ErrorMessages.LIMIT_MUST_BE_POSITIVE)  # limit 양수 오류를 알린다.
        for index, transaction in enumerate(self.transactions.iter_latest()):  # 최신 거래부터 번호를 붙여 한 건씩 읽는다.
            if index >= limit:  # 이미 요청한 개수만큼 전달했는지 확인한다.
                break  # 더 이상 파일을 읽지 않고 반복을 끝낸다.
            yield transaction  # 현재 거래 한 건만 호출한 쪽에 전달한다.

    def search_transactions(  # 여러 조건에 맞는 거래를 최신순으로 한 건씩 찾는다.
        self,  # 현재 서비스 객체 자신을 뜻한다.
        date_from: Optional[str] = None,  # 시작 날짜이며 생략할 수 있다.
        date_to: Optional[str] = None,  # 종료 날짜이며 생략할 수 있다.
        category: Optional[str] = None,  # 카테고리 조건이며 생략할 수 있다.
        transaction_type: Optional[str] = None,  # 거래 타입 조건이며 생략할 수 있다.
        query: Optional[str] = None,  # 메모에 포함될 검색어이며 생략할 수 있다.
        tag: Optional[str] = None,  # 반드시 포함할 태그이며 생략할 수 있다.
    ) -> Iterator[Transaction]:  # 조건을 만족한 거래를 제너레이터로 전달한다.
        checked_from: Optional[str] = None  # 검사된 시작 날짜가 없다는 상태로 시작한다.
        if date_from is not None:  # 사용자가 시작 날짜를 입력했는지 확인한다.
            checked_from = validate_date(date_from)  # 입력한 시작 날짜를 검사해서 저장한다.
        checked_to: Optional[str] = None  # 검사된 종료 날짜가 없다는 상태로 시작한다.
        if date_to is not None:  # 사용자가 종료 날짜를 입력했는지 확인한다.
            checked_to = validate_date(date_to)  # 입력한 종료 날짜를 검사해서 저장한다.
        checked_category: Optional[str] = None  # 검사된 카테고리 조건이 없다는 상태로 시작한다.
        if category is not None:  # 사용자가 카테고리 조건을 입력했는지 확인한다.
            checked_category = validate_category_name(category)  # 입력한 카테고리 이름을 검사해서 저장한다.
        checked_type: Optional[str] = None  # 검사된 거래 타입 조건이 없다는 상태로 시작한다.
        if transaction_type is not None:  # 사용자가 거래 타입 조건을 입력했는지 확인한다.
            checked_type = validate_transaction_type(transaction_type)  # 입력한 거래 타입을 검사해서 저장한다.
        checked_query: Optional[str] = None  # 검사된 메모 검색어가 없다는 상태로 시작한다.
        if query is not None:  # 사용자가 메모 검색어를 입력했는지 확인한다.
            checked_query = query.strip().lower()  # 앞뒤 공백을 지우고 소문자로 바꿔 저장한다.
        checked_tag: Optional[str] = None  # 검사된 태그 조건이 없다는 상태로 시작한다.
        if tag is not None:  # 사용자가 태그 조건을 입력했는지 확인한다.
            checked_tag = tag.strip()  # 태그 앞뒤 공백을 제거해서 저장한다.
        if checked_from and checked_to and checked_from > checked_to:  # 시작 날짜가 종료 날짜보다 뒤인지 검사한다.
            raise ValidationError(*ErrorMessages.DATE_RANGE_REVERSED)  # 날짜 순서 역전 오류를 알린다.
        for transaction in self.transactions.iter_latest():  # 최신 거래부터 파일을 한 건씩 읽는다.
            if checked_from and transaction.date < checked_from:  # 거래가 시작 날짜보다 이전인지 검사한다.
                continue  # 조건에 맞지 않으므로 다음 거래로 넘어간다.
            if checked_to and transaction.date > checked_to:  # 거래가 종료 날짜보다 이후인지 검사한다.
                continue  # 조건에 맞지 않으므로 다음 거래로 넘어간다.
            if checked_category and transaction.category != checked_category:  # 카테고리가 다른지 검사한다.
                continue  # 조건에 맞지 않으므로 다음 거래로 넘어간다.
            if checked_type and transaction.type != checked_type:  # 거래 타입이 다른지 검사한다.
                continue  # 조건에 맞지 않으므로 다음 거래로 넘어간다.
            if checked_query and checked_query not in transaction.memo.lower():  # 메모에 검색어가 없는지 검사한다.
                continue  # 조건에 맞지 않으므로 다음 거래로 넘어간다.
            if checked_tag and checked_tag not in transaction.tags:  # 거래 태그 목록에 찾는 태그가 없는지 검사한다.
                continue  # 조건에 맞지 않으므로 다음 거래로 넘어간다.
            yield transaction  # 모든 조건을 만족한 거래 한 건을 전달한다.

    def update_transaction(  # id로 찾은 거래의 전달된 필드만 수정한다.
        self,  # 현재 서비스 객체 자신을 뜻한다.
        transaction_id: str,  # 수정할 거래의 유일한 id다.
        date: Optional[str] = None,  # 새 날짜이며 생략하면 기존 값을 유지한다.
        transaction_type: Optional[str] = None,  # 새 타입이며 생략하면 기존 값을 유지한다.
        category: Optional[str] = None,  # 새 카테고리이며 생략하면 기존 값을 유지한다.
        amount: Optional[object] = None,  # 새 금액이며 생략하면 기존 값을 유지한다.
        memo: Optional[str] = None,  # 새 메모이며 생략하면 기존 값을 유지하고 빈 문자열이면 지운다.
        tags: Optional[object] = None,  # 새 태그이며 생략하면 기존 값을 유지하고 빈 문자열이면 지운다.
    ) -> Transaction:  # 수정과 저장을 마친 거래를 돌려준다.
        no_changes = (  # 수정 옵션이 하나도 없는지 단계별 조건으로 계산한다.
            date is None  # 새 날짜가 입력되지 않았는지 확인한다.
            and transaction_type is None  # 새 거래 타입이 입력되지 않았는지 확인한다.
            and category is None  # 새 카테고리가 입력되지 않았는지 확인한다.
            and amount is None  # 새 금액이 입력되지 않았는지 확인한다.
            and memo is None  # 새 메모가 입력되지 않았는지 확인한다.
            and tags is None  # 새 태그가 입력되지 않았는지 확인한다.
        )  # 모든 수정 옵션 확인을 끝낸다.
        if no_changes:  # 수정할 값이 하나도 없는지 확인한다.
            raise ValidationError(*ErrorMessages.NO_FIELDS_TO_UPDATE)  # 수정 항목 없음 오류를 발생시킨다.
        existing = self.transactions.find_by_id(transaction_id)  # id가 같은 기존 거래를 찾는다.
        if existing is None:  # 수정할 거래가 존재하지 않는지 검사한다.
            raise NotFoundError(*ErrorMessages.transaction_not_found(transaction_id))  # 거래 없음 오류를 발생시킨다.
        new_type = existing.type  # 새 거래 타입의 기본값으로 기존 타입을 저장한다.
        if transaction_type is not None:  # 새 거래 타입이 입력되었는지 확인한다.
            new_type = validate_transaction_type(transaction_type)  # 새 거래 타입을 검사해서 교체한다.
        new_date = existing.date  # 새 날짜의 기본값으로 기존 날짜를 저장한다.
        if date is not None:  # 새 날짜가 입력되었는지 확인한다.
            new_date = validate_date(date)  # 새 날짜를 검사해서 교체한다.
        new_amount = existing.amount  # 새 금액의 기본값으로 기존 금액을 저장한다.
        if amount is not None:  # 새 금액이 입력되었는지 확인한다.
            new_amount = validate_amount(amount)  # 새 금액을 검사해서 교체한다.
        new_category = existing.category  # 새 카테고리의 기본값으로 기존 카테고리를 저장한다.
        if category is not None:  # 새 카테고리가 입력되었는지 확인한다.
            new_category = self._checked_category(category)  # 새 카테고리 이름과 등록 여부를 검사해서 교체한다.
        new_memo = existing.memo  # 새 메모의 기본값으로 기존 메모를 저장한다.
        if memo is not None:  # 새 메모가 입력되었는지 확인한다.
            new_memo = str(memo).strip()  # 새 메모의 앞뒤 공백을 제거해서 교체한다.
        new_tags = list(existing.tags)  # 새 태그의 기본값으로 기존 태그 목록을 복사한다.
        if tags is not None:  # 새 태그가 입력되었는지 확인한다.
            new_tags = normalize_tags(tags)  # 새 태그를 정리해서 교체한다.
        replacement = Transaction(  # 변경된 값과 유지할 값을 합쳐 새 거래 객체를 만든다.
            id=existing.id,  # 거래 id는 수정하지 않고 그대로 유지한다.
            type=new_type,  # 위에서 결정한 거래 타입을 저장한다.
            date=new_date,  # 위에서 결정한 날짜를 저장한다.
            amount=new_amount,  # 위에서 결정한 금액을 저장한다.
            category=new_category,  # 위에서 결정한 카테고리를 저장한다.
            memo=new_memo,  # 위에서 결정한 메모를 저장한다.
            tags=new_tags,  # 위에서 결정한 태그 목록을 저장한다.
        )  # 교체할 거래 객체 만들기를 끝낸다.
        self.transactions.replace(replacement)  # 임시 파일과 원자적 교체 방식으로 기존 거래를 수정한다.
        return replacement  # 화면 출력이나 테스트에 쓸 수 있도록 수정한 거래를 돌려준다.

    def delete_transaction(self, transaction_id: str) -> None:  # id가 같은 거래 한 건을 삭제한다.
        if not self.transactions.delete(transaction_id):  # 저장소가 삭제 대상을 찾지 못했는지 검사한다.
            raise NotFoundError(*ErrorMessages.transaction_not_found(transaction_id))  # 거래 없음 오류를 발생시킨다.

    def monthly_summary(self, month: str, top: int) -> MonthlySummary:  # 한 달의 수입, 지출, 카테고리 합계, 예산을 계산한다.
        checked_month = validate_month(month)  # 계산할 월을 YYYY-MM 형식으로 검사한다.
        if top <= 0:  # 상위 카테고리 개수가 0 또는 음수인지 검사한다.
            raise ValidationError(*ErrorMessages.TOP_MUST_BE_POSITIVE)  # top 양수 오류를 알린다.
        total_income = 0  # 총수입 계산을 0에서 시작한다.
        total_expense = 0  # 총지출 계산을 0에서 시작한다.
        transaction_count = 0  # 해당 월의 거래 개수 계산을 0에서 시작한다.
        category_totals: Dict[str, int] = {}  # 지출 카테고리별 합계를 담을 빈 사전을 만든다.
        for transaction in self.transactions.iter_latest():  # 거래 파일을 최신순으로 한 건씩 읽는다.
            if not transaction.date.startswith(checked_month + "-"):  # 거래가 계산 대상 월에 속하는지 검사한다.
                continue  # 다른 월의 거래는 건너뛴다.
            transaction_count += 1  # 대상 월의 거래 개수에 1을 더한다.
            if transaction.type == "income":  # 현재 거래가 수입인지 검사한다.
                total_income += transaction.amount  # 수입 금액을 총수입에 더한다.
            else:  # income이 아니면 검증된 값은 expense다.
                total_expense += transaction.amount  # 지출 금액을 총지출에 더한다.
                previous_total = category_totals.get(transaction.category, 0)  # 현재 카테고리의 이전 지출 합계를 가져온다.
                new_total = previous_total + transaction.amount  # 이전 합계에 현재 거래 금액을 더한다.
                category_totals[transaction.category] = new_total  # 계산한 새 합계를 카테고리 사전에 저장한다.
        sorted_categories = list(category_totals.items())  # 카테고리와 합계 쌍을 정렬 가능한 목록으로 만든다.
        sorted_categories.sort(key=_category_expense_sort_key)  # 별도 함수의 쉬운 기준으로 지출 목록을 정렬한다.
        top_categories = sorted_categories[:top]  # 정렬된 목록 앞에서 사용자가 요청한 개수만 선택한다.
        return MonthlySummary(  # 계산 결과를 월별 요약 객체로 묶어서 돌려준다.
            month=checked_month,  # 검사한 계산 대상 월을 저장한다.
            total_income=total_income,  # 계산한 총수입을 저장한다.
            total_expense=total_expense,  # 계산한 총지출을 저장한다.
            category_expenses=top_categories,  # 계산한 상위 카테고리 목록을 저장한다.
            budget=self.budgets.get(checked_month),  # 저장된 월 예산을 찾아서 저장한다.
            transaction_count=transaction_count,  # 계산한 거래 개수를 저장한다.
        )  # 월별 요약 객체 만들기를 끝낸다.

    def set_budget(self, month: str, amount: object) -> int:  # 월 예산을 새로 저장하거나 기존 값을 수정한다.
        return self.budgets.set(month, amount)  # 예산 저장소에 검증과 저장을 맡기고 실제 금액을 돌려준다.

    def get_budget(self, month: str) -> Optional[int]:  # 특정 월의 예산을 조회한다.
        return self.budgets.get(month)  # 예산 저장소에서 금액을 찾아서 돌려준다.

    def add_category(self, name: str) -> str:  # 새 카테고리를 검사하고 저장한다.
        cleaned = validate_category_name(name)  # 이름의 공백과 길이를 검사한다.
        self.categories.add(cleaned)  # 카테고리 저장소에 중복 검사와 저장을 맡긴다.
        return cleaned  # 실제 저장한 이름을 돌려준다.

    def list_categories(self) -> List[str]:  # 저장된 모든 카테고리를 조회한다.
        return self.categories.list_all()  # 카테고리 저장소가 정렬한 목록을 그대로 돌려준다.

    def remove_category(self, name: str) -> None:  # 사용하지 않는 카테고리만 삭제한다.
        cleaned = validate_category_name(name)  # 삭제할 이름의 형식을 검사한다.
        for transaction in self.transactions.iter_latest():  # 거래 파일을 한 건씩 읽는다.
            if transaction.category == cleaned:  # 삭제할 카테고리를 사용 중인 거래가 있는지 검사한다.
                raise ConflictError(*ErrorMessages.category_in_use(cleaned))  # 사용 중인 카테고리 삭제 불가 오류를 발생시킨다.
        if not self.categories.remove(cleaned):  # 사용 중이 아니지만 등록 목록에도 없는지 검사한다.
            raise NotFoundError(*ErrorMessages.category_not_found(cleaned))  # 카테고리 없음 오류를 발생시킨다.



    def import_csv(self, source: Path) -> Tuple[int, int, List[str]]:  # CSV 거래를 검사하면서 한 건씩 가져온다.
        imported = 0  # 정상적으로 저장한 거래 개수를 0에서 시작한다.
        skipped = 0  # 잘못되어 건너뛴 거래 개수를 0에서 시작한다.
        errors: List[str] = []  # 건너뛴 줄의 이유를 담을 빈 목록을 만든다.
        
        # BOM(Byte Order Mark)이란 무엇인가?
        # BOM = Byte Order Mark (바이트 순서 표식)
            # Byte = 컴퓨터가 데이터를 다루는 기본 8자리 묶음 단위
            # Order = 순서 (저장 순서)
            # Mark = 표식 (도장, 꼬리표)

        # utf-8-sig = BOM 도장을 자동으로 제거하고 순수 데이터만 정상 읽기
        with source.open("r", encoding="utf-8-sig", newline="") as csv_file:  # UTF-8과 선택적 BOM을 지원하는 CSV 읽기 모드로 연다.
            reader = csv.DictReader(csv_file)  # 헤더 이름을 열쇠로 사용하는 사전 형태로 한 줄씩 읽는다.
            headers = set(reader.fieldnames or [])  # 파일에 실제로 있는 헤더 이름을 집합으로 만든다.
            missing = CSV_REQUIRED_COLUMNS - headers  # 반드시 필요한데 빠진 헤더를 계산한다.
        
            if missing:  # 빠진 필수 헤더가 하나 이상 있는지 검사한다.
                missing_text = ", ".join(sorted(missing))  # 빠진 이름들을 읽기 좋은 쉼표 문자열로 만든다.
                raise ValidationError(*ErrorMessages.csv_missing_headers(missing_text))  # 헤더 누락 오류를 발생시킨다.
        
            for line_number, row in enumerate(reader, start=2):  # 헤더 다음인 2번 줄부터 번호를 붙여 한 건씩 읽는다.
                try:  # 현재 CSV 줄의 검사와 저장을 시도한다.
                    self.add_transaction(  # 기존 add 규칙을 재사용해서 CSV 거래 한 건을 저장한다.
                        date=row.get("date") or "",  # date 열이 없거나 비었으면 검증에서 잡도록 빈 문자열을 전달한다.
                        transaction_type=row.get("type") or "",  # type 열이 없거나 비었으면 빈 문자열을 전달한다.
                        category=row.get("category") or "",  # category 열이 없거나 비었으면 빈 문자열을 전달한다.
                        amount=row.get("amount") or "",  # amount 열이 없거나 비었으면 빈 문자열을 전달한다.
                        memo=row.get("memo") or "",  # 선택 메모가 없으면 빈 문자열을 전달한다.
                        tags=row.get("tags") or "",  # 선택 태그가 없으면 빈 문자열을 전달한다.
                    )  # CSV 거래 한 건 저장을 끝낸다.
                    imported += 1  # 정상 저장 개수에 1을 더한다.
                except BudgetAppError as error:  # 현재 줄의 예상 가능한 입력 오류를 잡는다.
                    skipped += 1  # 건너뛴 개수에 1을 더한다.
                    errors.append(f"line={line_number}: {error.message}")  # 줄 번호와 원인을 기록한다.
        
        return imported, skipped, errors  # 저장 수, 건너뜀 수, 이유 목록을 함께 돌려준다.



    def export_csv(  # 조건에 맞는 거래를 고정 스키마 CSV 파일로 내보낸다.
        self,  # 현재 서비스 객체 자신을 뜻한다.
        output: Path,  # 새로 만들 CSV 파일 경로다.
        month: Optional[str] = None,  # YYYY-MM 월 조건이며 생략할 수 있다.
        date_from: Optional[str] = None,  # 시작 날짜 조건이며 범위 사용 때 필요하다.
        date_to: Optional[str] = None,  # 종료 날짜 조건이며 범위 사용 때 필요하다.
    ) -> int:  # 실제로 CSV에 쓴 거래 개수를 돌려준다.
        
        if not month and not date_from and not date_to:  # 내보내기 조건이 하나도 없는지 검사한다.
            raise ValidationError(*ErrorMessages.EXPORT_CONDITION_REQUIRED)  # 내보내기 조건 필요 오류를 발생시킨다.
        if bool(date_from) != bool(date_to):  # 시작과 종료 날짜 중 하나만 입력했는지 검사한다.
            raise ValidationError(*ErrorMessages.EXPORT_DATE_RANGE_INCOMPLETE)  # 기간 조건 불완전 오류를 발생시킨다.
        checked_month: Optional[str] = None  # 검사된 월 조건이 없다는 상태로 시작한다.
        if month is not None:  # 사용자가 월 조건을 입력했는지 확인한다.
            checked_month = validate_month(month)  # 입력한 월을 검사해서 저장한다.
        checked_from: Optional[str] = None  # 검사된 시작 날짜가 없다는 상태로 시작한다.
        if date_from is not None:  # 사용자가 시작 날짜를 입력했는지 확인한다.
            checked_from = validate_date(date_from)  # 입력한 시작 날짜를 검사해서 저장한다.
        checked_to: Optional[str] = None  # 검사된 종료 날짜가 없다는 상태로 시작한다.
        if date_to is not None:  # 사용자가 종료 날짜를 입력했는지 확인한다.
            checked_to = validate_date(date_to)  # 입력한 종료 날짜를 검사해서 저장한다.
        if checked_from and checked_to and checked_from > checked_to:  # 시작 날짜가 종료 날짜보다 뒤인지 검사한다.
            raise ValidationError(*ErrorMessages.DATE_RANGE_REVERSED)  # 날짜 순서 역전 오류를 발생시킨다.
        
        output.parent.mkdir(parents=True, exist_ok=True)  # 출력 파일의 부모 폴더가 없으면 자동으로 만든다.
        
        exported = 0  # CSV에 쓴 거래 개수를 0에서 시작한다.


        with output.open("w", encoding="utf-8", newline="") as csv_file:  # UTF-8 CSV 새 파일을 쓰기 모드로 연다.
            writer = csv.DictWriter(csv_file, fieldnames=CSV_COLUMNS)  # 고정 열 순서를 사용하는 CSV 작성기를 만든다.
            writer.writeheader()  # 첫 줄에 고정 CSV 헤더를 쓴다.
            for transaction in self.transactions.iter_latest():  # 최신 거래부터 한 건씩 읽는다.
                if checked_month and not transaction.date.startswith(checked_month + "-"):  # 월 조건에 맞지 않는지 검사한다.
                    continue  # 다른 월의 거래는 건너뛴다.
                if checked_from and transaction.date < checked_from:  # 시작 날짜보다 이전 거래인지 검사한다.
                    continue  # 기간 밖의 거래는 건너뛴다.
                if checked_to and transaction.date > checked_to:  # 종료 날짜보다 이후 거래인지 검사한다.
                    continue  # 기간 밖의 거래는 건너뛴다.
                writer.writerow(  # 요구사항의 여섯 열에 맞춰 거래 한 건을 CSV에 쓴다.
                    {  # 열 이름과 쓸 값을 한 쌍으로 만든다.
                        "date": transaction.date,  # 거래 날짜를 date 열에 쓴다.
                        "type": transaction.type,  # 거래 타입을 type 열에 쓴다.
                        "category": transaction.category,  # 카테고리를 category 열에 쓴다.
                        "amount": transaction.amount,  # 거래 금액을 amount 열에 쓴다.
                        "memo": transaction.memo,  # 메모를 memo 열에 쓴다.
                        "tags": ",".join(transaction.tags),  # 태그 목록을 쉼표 구분 문자열로 바꿔 tags 열에 쓴다.
                    }  # CSV 한 행에 쓸 사전 만들기를 끝낸다.
                )  # CSV 한 행 쓰기를 끝낸다.
                exported += 1  # 내보낸 거래 개수에 1을 더한다.
        return exported  # 실제로 쓴 거래 개수를 돌려준다.
