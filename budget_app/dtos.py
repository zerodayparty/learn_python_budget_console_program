# 이 파일은 CLI와 서비스 사이에서 거래 입력값을 한 상자로 전달하는 DTO들을 정의한다.

from dataclasses import dataclass  # dataclass는 데이터 보관용 클래스를 간단하게 만드는 Python 표준 도구다.
from typing import Optional, Tuple  # 값이 없을 수 있는 타입과 바꿀 수 없는 문자열 묶음 타입을 표시하기 위해 가져온다.

from budget_app.constants import ErrorMessages  # 여러 입력값을 함께 검사할 때 사용할 오류 메시지를 가져온다.
from budget_app.exceptions import ValidationError  # 올바르지 않은 입력을 같은 형식으로 알리기 위해 가져온다.
from budget_app.validators import (  # DTO가 원시 입력값을 안전한 값으로 바꿀 검증 함수들을 가져온다.
    normalize_tags,  # 쉼표 문자열이나 목록 형태의 태그를 문자열 목록으로 정리한다.
    validate_amount,  # 금액을 0보다 큰 정수로 검사하고 변환한다.
    validate_category_name,  # 카테고리 이름의 공백, 길이, 줄바꿈을 검사한다.
    validate_date,  # 날짜가 YYYY-MM-DD 형식의 실제 날짜인지 검사한다.
    validate_transaction_type,  # 거래 타입이 income 또는 expense인지 검사한다.
)  # DTO에서 사용할 검증 함수 가져오기를 끝낸다.


def _optional_date(value: Optional[str]) -> Optional[str]:  # 생략 가능한 날짜를 검사한다.
    return validate_date(value) if value is not None else None  # 값이 있을 때만 날짜 검증을 실행한다.


def _optional_transaction_type(value: Optional[str]) -> Optional[str]:  # 생략 가능한 거래 타입을 검사한다.
    return validate_transaction_type(value) if value is not None else None  # 값이 있을 때만 타입 검증을 실행한다.


def _optional_category(value: Optional[str]) -> Optional[str]:  # 생략 가능한 카테고리 이름을 검사한다.
    return validate_category_name(value) if value is not None else None  # 값이 있을 때만 이름 검증을 실행한다.


def _optional_amount(value: Optional[object]) -> Optional[int]:  # 생략 가능한 금액을 검사한다.
    return validate_amount(value) if value is not None else None  # 값이 있을 때만 양의 정수 검증을 실행한다.


def _optional_text(value: Optional[str]) -> Optional[str]:  # 생략 가능한 일반 문자열의 앞뒤 공백을 정리한다.
    return str(value).strip() if value is not None else None  # 값이 있을 때만 문자열로 바꾸고 공백을 제거한다.


def _optional_tags(value: Optional[object]) -> Optional[Tuple[str, ...]]:  # 생략 가능한 태그를 바꿀 수 없는 문자열 묶음으로 정리한다.
    return tuple(normalize_tags(value)) if value is not None else None  # 값이 있을 때만 태그를 정리하고 튜플로 고정한다.


@dataclass(frozen=True)  # 만든 뒤 값이 바뀌지 않는 거래 추가 요청 DTO를 선언한다.
class CreateTransactionDTO:  # CLI에서 서비스로 거래 추가 데이터를 한 번에 전달하는 상자다.
    date: str  # 검증 전 또는 검증 후 거래 날짜를 담는다.
    transaction_type: str  # 검증 전 또는 검증 후 수입·지출 타입을 담는다.
    category: str  # 검증 전 또는 검증 후 카테고리 이름을 담는다.
    amount: object  # 문자열 또는 정수로 들어올 수 있는 금액을 담는다.
    memo: str = ""  # 선택 메모를 담고 생략하면 빈 문자열을 사용한다.
    tags: Optional[object] = None  # 선택 태그 문자열이나 목록을 담고 생략할 수 있다.

    def __post_init__(self) -> None:  # DTO를 만든 직후 모든 입력을 검사하고 정리한다.
        object.__setattr__(self, "date", validate_date(self.date))  # frozen DTO 안에 검증된 날짜를 저장한다.
        object.__setattr__(self, "transaction_type", validate_transaction_type(self.transaction_type))  # 검증된 거래 타입을 저장한다.
        object.__setattr__(self, "category", validate_category_name(self.category))  # 검증된 카테고리 이름을 저장한다.
        object.__setattr__(self, "amount", validate_amount(self.amount))  # 정수로 변환하고 검증한 금액을 저장한다.
        object.__setattr__(self, "memo", str(self.memo).strip())  # 메모의 앞뒤 공백을 제거해서 저장한다.
        object.__setattr__(self, "tags", tuple(normalize_tags(self.tags)))  # 태그를 중복 없는 문자열 튜플로 바꿔 저장한다.


@dataclass(frozen=True)  # 만든 뒤 조건이 바뀌지 않는 거래 검색 DTO를 선언한다.
class SearchTransactionsDTO:  # CLI에서 서비스로 검색 조건들을 한 번에 전달하는 상자다.
    date_from: Optional[str] = None  # 검색 시작 날짜이며 생략할 수 있다.
    date_to: Optional[str] = None  # 검색 종료 날짜이며 생략할 수 있다.
    category: Optional[str] = None  # 찾을 카테고리이며 생략할 수 있다.
    transaction_type: Optional[str] = None  # 찾을 거래 타입이며 생략할 수 있다.
    query: Optional[str] = None  # 메모에서 찾을 글자이며 생략할 수 있다.
    tag: Optional[str] = None  # 반드시 포함할 태그이며 생략할 수 있다.

    def __post_init__(self) -> None:  # DTO를 만든 직후 전달된 검색 조건만 검사하고 정리한다.
        object.__setattr__(self, "date_from", _optional_date(self.date_from))  # 시작 날짜가 있으면 검사해서 저장한다.
        object.__setattr__(self, "date_to", _optional_date(self.date_to))  # 종료 날짜가 있으면 검사해서 저장한다.
        object.__setattr__(self, "category", _optional_category(self.category))  # 카테고리가 있으면 검사해서 저장한다.
        object.__setattr__(self, "transaction_type", _optional_transaction_type(self.transaction_type))  # 거래 타입이 있으면 검사해서 저장한다.
        object.__setattr__(self, "query", _optional_text(self.query))  # 메모 검색어가 있으면 공백을 정리해서 저장한다.
        object.__setattr__(self, "tag", _optional_text(self.tag))  # 태그 검색어가 있으면 공백을 정리해서 저장한다.
        if self.date_from and self.date_to and self.date_from > self.date_to:  # 시작 날짜가 종료 날짜보다 뒤인지 확인한다.
            raise ValidationError(*ErrorMessages.DATE_RANGE_REVERSED)  # 잘못된 날짜 순서를 입력 오류로 알린다.

@dataclass(frozen=True)  # 만든 뒤 값이 바뀌지 않는 거래 수정 요청 DTO를 선언한다.
class UpdateTransactionDTO:  # CLI에서 서비스로 거래 수정 데이터를 한 번에 전달하는 상자다.
    transaction_id: str  # 수정할 거래를 찾는 고유 식별자를 담는다.
    date: Optional[str] = None  # 새 날짜이며 생략하면 기존 값을 유지한다.
    transaction_type: Optional[str] = None  # 새 거래 타입이며 생략하면 기존 값을 유지한다.
    category: Optional[str] = None  # 새 카테고리이며 생략하면 기존 값을 유지한다.
    amount: Optional[object] = None  # 새 금액이며 생략하면 기존 값을 유지한다.
    memo: Optional[str] = None  # 새 메모이며 생략하면 기존 값을 유지한다.
    tags: Optional[object] = None  # 새 태그이며 생략하면 기존 값을 유지한다.

    def __post_init__(self) -> None:  # DTO를 만든 직후 전달된 수정 값만 검사하고 정리한다.
        object.__setattr__(self, "transaction_id", self.transaction_id.strip())  # 거래 id 앞뒤의 불필요한 공백을 제거한다.
        object.__setattr__(self, "date", _optional_date(self.date))  # 새 날짜가 있으면 검사해서 저장한다.
        object.__setattr__(self, "transaction_type", _optional_transaction_type(self.transaction_type))  # 새 타입이 있으면 검사해서 저장한다.
        object.__setattr__(self, "category", _optional_category(self.category))  # 새 카테고리가 있으면 검사해서 저장한다.
        object.__setattr__(self, "amount", _optional_amount(self.amount))  # 새 금액이 있으면 검사해서 저장한다.
        object.__setattr__(self, "memo", _optional_text(self.memo))  # 새 메모가 있으면 공백을 정리해서 저장한다.
        object.__setattr__(self, "tags", _optional_tags(self.tags))  # 새 태그가 있으면 목록으로 정리해서 저장한다.

    @property  # 메서드를 괄호 없이 읽을 수 있는 계산 속성으로 만든다.
    def has_changes(self) -> bool:  # 수정할 필드가 하나라도 전달되었는지 계산한다.
        return any(  # 아래 값 중 하나라도 None이 아니면 참을 돌려준다.
            value is not None  # 현재 값이 실제로 전달되었는지 확인한다.
            for value in [self.date, self.transaction_type, self.category, self.amount, self.memo, self.tags]  # 수정 가능한 필드만 검사한다.
        )  # 변경 여부 계산을 끝낸다.
