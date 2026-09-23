# 이 파일은 거래 추가, 목록, 검색, 수정, 삭제 업무 규칙만 담당한다.

import uuid  # uuid는 다른 거래와 겹칠 가능성이 매우 낮은 식별자를 만드는 표준 도구다.
from typing import Iterator, Optional  # 거래 반복 반환과 찾지 못한 경우의 타입을 표시한다.

from budget_app.constants import ErrorMessages  # 거래 업무 규칙 오류 메시지를 가져온다.
from budget_app.dtos import CreateTransactionDTO, SearchTransactionsDTO, UpdateTransactionDTO  # 거래 입력을 묶고 검증한 DTO들을 가져온다.
from budget_app.exceptions import NotFoundError, ValidationError  # 거래 없음과 업무 규칙 오류를 알리기 위해 가져온다.
from budget_app.models import Transaction  # 거래 데이터 모델을 가져온다.
from budget_app.repositories import CategoryStore, TransactionRepository  # 거래와 카테고리 저장소를 가져온다.


def _matches_search(transaction: Transaction, criteria: SearchTransactionsDTO) -> bool:  # 거래 한 건이 모든 검색 조건과 일치하는지 계산한다.
    return (  # 모든 검색 조건을 동시에 만족할 때만 참을 돌려준다.
        (criteria.date_from is None or transaction.date >= criteria.date_from)  # 시작 날짜가 없거나 거래 날짜가 시작 날짜 이후인지 확인한다.
        and (criteria.date_to is None or transaction.date <= criteria.date_to)  # 종료 날짜가 없거나 거래 날짜가 종료 날짜 이전인지 확인한다.
        and (criteria.category is None or transaction.category == criteria.category)  # 카테고리가 없거나 같은 카테고리인지 확인한다.
        and (criteria.transaction_type is None or transaction.type == criteria.transaction_type)  # 타입이 없거나 같은 타입인지 확인한다.
        and (criteria.query is None or criteria.query.lower() in transaction.memo.lower())  # 검색어가 없거나 메모에 포함되는지 확인한다.
        and (criteria.tag is None or criteria.tag in transaction.tags)  # 태그가 없거나 거래 태그 목록에 포함되는지 확인한다.
    )  # 검색 조건 비교를 끝낸다.


class TransactionService:  # 거래 관련 업무 규칙과 저장 흐름을 담당한다.
    def __init__(self, transactions: TransactionRepository, categories: CategoryStore) -> None:  # 거래와 카테고리 저장소를 받는다.
        self._transactions = transactions  # 거래 저장소를 내부 전용 변수에 보관한다.
        self._categories = categories  # 카테고리 저장소를 내부 전용 변수에 보관한다.

    def _new_id(self) -> str:  # 다른 거래와 겹칠 가능성이 매우 낮은 새 id를 만든다.
        while True:  # 저장된 거래와 겹치지 않는 id가 만들어질 때까지 반복한다.
            candidate = f"TX-{uuid.uuid4().hex[:12].upper()}"  # UUID 앞 12자에 TX 접두사를 붙여 후보를 만든다.
            if self._transactions.find_by_id(candidate) is None:  # 후보 id가 기존 거래에 없는지 확인한다.
                return candidate  # 겹치지 않는 후보를 새 거래 id로 돌려준다.

    def _require_registered_category(self, category: str) -> None:  # 카테고리가 실제 등록 목록에 있는지 검사한다.
        if not self._categories.exists(category):  # DTO가 정리한 카테고리가 등록되어 있는지 확인한다.
            raise ValidationError(*ErrorMessages.unregistered_category(category))  # 미등록 카테고리 오류를 알린다.

    def add(self, request: CreateTransactionDTO) -> Transaction:  # 거래 추가 DTO 한 개를 받아 새 거래를 저장한다.
        self._require_registered_category(request.category)  # 등록된 카테고리만 거래에 사용할 수 있다는 규칙을 검사한다.
        transaction = Transaction(  # DTO의 검증된 값으로 새 거래 모델을 만든다.
            id=self._new_id(),  # 겹치지 않는 새 거래 id를 저장한다.
            date=request.date,  # DTO가 검증한 날짜를 저장한다.
            type=request.transaction_type,  # DTO가 검증한 거래 타입을 저장한다.
            category=request.category,  # DTO가 검증한 카테고리를 저장한다.
            amount=request.amount,  # DTO가 정수로 바꾼 금액을 저장한다.
            memo=request.memo,  # DTO가 정리한 메모를 저장한다.
            tags=list(request.tags or ()),  # DTO의 태그 튜플을 거래 모델용 목록으로 바꿔 저장한다.
        )  # 새 거래 모델 만들기를 끝낸다.
        self._transactions.append(transaction)  # 거래 저장소에 새 거래를 추가한다.
        return transaction  # 저장한 거래를 화면 출력과 테스트에 사용할 수 있도록 돌려준다.

    def list(self, limit: int) -> Iterator[Transaction]:  # 최신 거래를 요청한 개수만큼 한 건씩 전달한다.
        if limit <= 0:  # 제한 개수가 0 또는 음수인지 확인한다.
            raise ValidationError(*ErrorMessages.LIMIT_MUST_BE_POSITIVE)  # 양수 제한 개수 오류를 알린다.
        for index, transaction in enumerate(self._transactions.iter_latest()):  # 최신 거래부터 번호를 붙여 읽는다.
            if index >= limit:  # 이미 요청한 개수만큼 전달했는지 확인한다.
                break  # 더 이상 파일을 읽지 않고 반복을 끝낸다.
            yield transaction  # 현재 거래 한 건을 호출한 쪽에 전달한다.

    def search(self, criteria: SearchTransactionsDTO) -> Iterator[Transaction]:  # 검색 DTO의 조건과 맞는 거래를 최신순으로 찾는다.
        for transaction in self._transactions.iter_latest():  # 최신 거래부터 한 건씩 읽는다.
            if _matches_search(transaction, criteria):  # 현재 거래가 모든 검색 조건과 일치하는지 확인한다.
                yield transaction  # 조건을 만족한 거래만 호출한 쪽에 전달한다.

    def get(self, transaction_id: str) -> Optional[Transaction]:  # id가 같은 거래 한 건을 찾는다.
        return self._transactions.find_by_id(transaction_id)  # 거래 저장소의 조회 결과를 그대로 돌려준다.

    def update(self, request: UpdateTransactionDTO) -> Transaction:  # 거래 수정 DTO 한 개를 받아 기존 거래를 바꾼다.
        if not request.has_changes:  # DTO 안에 수정할 값이 하나도 없는지 확인한다.
            raise ValidationError(*ErrorMessages.NO_FIELDS_TO_UPDATE)  # 수정 항목 없음 오류를 알린다.
        existing = self._transactions.find_by_id(request.transaction_id)  # DTO의 id와 같은 기존 거래를 찾는다.
        if existing is None:  # 수정할 거래가 존재하지 않는지 확인한다.
            raise NotFoundError(*ErrorMessages.transaction_not_found(request.transaction_id))  # 거래 없음 오류를 알린다.
        if request.category is not None:  # 카테고리를 실제로 변경하려는 요청인지 확인한다.
            self._require_registered_category(request.category)  # 새 카테고리가 등록되어 있는지 검사한다.
        replacement = Transaction(  # 변경 값과 기존 값을 합쳐 교체할 거래 모델을 만든다.
            id=existing.id,  # 거래 id는 바꾸지 않고 유지한다.
            type=request.transaction_type if request.transaction_type is not None else existing.type,  # 새 타입이 있으면 바꾸고 없으면 유지한다.
            date=request.date if request.date is not None else existing.date,  # 새 날짜가 있으면 바꾸고 없으면 유지한다.
            amount=request.amount if request.amount is not None else existing.amount,  # 새 금액이 있으면 바꾸고 없으면 유지한다.
            category=request.category if request.category is not None else existing.category,  # 새 카테고리가 있으면 바꾸고 없으면 유지한다.
            memo=request.memo if request.memo is not None else existing.memo,  # 새 메모가 있으면 바꾸고 없으면 유지한다.
            tags=list(request.tags) if request.tags is not None else list(existing.tags),  # 새 태그가 있으면 바꾸고 없으면 기존 목록을 복사한다.
        )  # 교체할 거래 모델 만들기를 끝낸다.
        self._transactions.replace(replacement)  # 거래 저장소에서 기존 거래를 새 거래로 교체한다.
        return replacement  # 수정된 거래를 화면 출력과 테스트에 사용할 수 있도록 돌려준다.

    def delete(self, transaction_id: str) -> None:  # id가 같은 거래 한 건을 삭제한다.
        if not self._transactions.delete(transaction_id):  # 저장소가 삭제 대상을 찾지 못했는지 확인한다.
            raise NotFoundError(*ErrorMessages.transaction_not_found(transaction_id))  # 거래 없음 오류를 알린다.
