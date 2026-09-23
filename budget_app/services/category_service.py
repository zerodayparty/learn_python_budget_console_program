# 이 파일은 카테고리 추가, 목록, 존재 확인, 삭제 업무 규칙만 담당한다.

from typing import List  # 카테고리 이름 목록 반환 타입을 표시한다.

from budget_app.constants import ErrorMessages  # 카테고리 업무 규칙 오류 메시지를 가져온다.
from budget_app.exceptions import ConflictError, NotFoundError  # 사용 중 충돌과 카테고리 없음 오류를 알리기 위해 가져온다.
from budget_app.repositories import CategoryStore, TransactionRepository  # 카테고리와 거래 저장소를 가져온다.
from budget_app.validators import validate_category_name  # 카테고리 이름 검증 함수를 가져온다.


class CategoryService:  # 카테고리 관리 업무 규칙을 담당한다.
    def __init__(self, categories: CategoryStore, transactions: TransactionRepository) -> None:  # 카테고리와 거래 저장소를 받는다.
        self._categories = categories  # 카테고리 저장소를 내부 전용 변수에 보관한다.
        self._transactions = transactions  # 카테고리 사용 여부 확인용 거래 저장소를 보관한다.

    def add(self, name: str) -> str:  # 새 카테고리를 검사하고 저장한다.
        cleaned = validate_category_name(name)  # 카테고리 이름의 공백과 길이를 검사한다.
        self._categories.add(cleaned)  # 카테고리 저장소에 중복 검사와 저장을 맡긴다.
        return cleaned  # 실제 저장한 카테고리 이름을 돌려준다.

    def list(self) -> List[str]:  # 저장된 모든 카테고리를 조회한다.
        return self._categories.list_all()  # 카테고리 저장소가 정렬한 목록을 돌려준다.

    def exists(self, name: str) -> bool:  # 특정 카테고리가 등록되어 있는지 확인한다.
        cleaned = validate_category_name(name)  # 확인할 카테고리 이름을 검사하고 정리한다.
        return self._categories.exists(cleaned)  # 저장소에서 이름 존재 여부를 확인해 돌려준다.

    def remove(self, name: str) -> None:  # 사용하지 않는 카테고리만 삭제한다.
        cleaned = validate_category_name(name)  # 삭제할 카테고리 이름을 검사하고 정리한다.
        for transaction in self._transactions.iter_latest():  # 저장된 거래를 최신순으로 한 건씩 읽는다.
            if transaction.category == cleaned:  # 삭제할 카테고리를 사용 중인 거래가 있는지 확인한다.
                raise ConflictError(*ErrorMessages.category_in_use(cleaned))  # 사용 중인 카테고리 삭제 오류를 알린다.
        if not self._categories.remove(cleaned):  # 카테고리 저장소에서 삭제 대상을 찾지 못했는지 확인한다.
            raise NotFoundError(*ErrorMessages.category_not_found(cleaned))  # 카테고리 없음 오류를 알린다.
