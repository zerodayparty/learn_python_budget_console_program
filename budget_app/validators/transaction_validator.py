# 이 파일은 거래 금액, 거래 타입, 태그 입력만 검사하고 정리한다.

from typing import List, Optional  # 태그 목록과 생략 가능한 값을 표시하기 위해 가져온다.

from budget_app.constants import ALLOWED_TYPES, ErrorMessages  # 허용 거래 타입과 오류 메시지를 가져온다.
from budget_app.exceptions import ValidationError  # 잘못된 거래 입력을 같은 오류 형식으로 알리기 위해 가져온다.


def validate_amount(value: object) -> int:  # 금액을 0보다 큰 정수로 바꿔서 돌려준다.
    if isinstance(value, bool):  # True와 False는 Python에서 숫자로 취급되므로 먼저 막는다.
        raise ValidationError(*ErrorMessages.AMOUNT_MUST_BE_NUMBER)  # 숫자가 아닌 자료형 오류를 알린다.
    try:  # 입력값을 정수로 바꾸는 작업을 시도한다.
        amount = int(str(value).strip())  # 입력값을 문자열로 정리한 뒤 정수로 변환한다.
    except (TypeError, ValueError) as error:  # 정수로 바꿀 수 없는 입력 오류를 잡는다.
        raise ValidationError(*ErrorMessages.AMOUNT_MUST_BE_INTEGER) from error  # 정수 입력 오류로 바꿔 알린다.
    if amount <= 0:  # 금액이 0이거나 음수인지 확인한다.
        raise ValidationError(*ErrorMessages.AMOUNT_MUST_BE_POSITIVE)  # 양수 금액 규칙 오류를 알린다.
    return amount  # 검사를 통과한 양의 정수를 돌려준다.


def validate_transaction_type(value: str) -> str:  # 거래 타입이 income 또는 expense인지 검사한다.
    cleaned = value.strip().lower()  # 앞뒤 공백을 제거하고 소문자로 바꾼다.
    if cleaned not in ALLOWED_TYPES:  # 허용 목록에 없는 거래 타입인지 확인한다.
        raise ValidationError(*ErrorMessages.INVALID_TRANSACTION_TYPE)  # 올바르지 않은 거래 타입 오류를 알린다.
    return cleaned  # 검사를 통과한 거래 타입을 돌려준다.


def normalize_tags(value: object) -> List[str]:  # 태그를 중복 없는 문자열 목록으로 정리한다.
    if value is None:  # 태그가 생략되었는지 확인한다.
        return []  # 생략된 태그를 빈 목록으로 바꾼다.
    if isinstance(value, list):  # 저장 파일에서 읽은 값이 이미 목록인지 확인한다.
        raw_tags = [str(item) for item in value]  # 각 목록 값을 문자열로 바꾼다.
    else:  # 콘솔이나 CSV의 쉼표 구분 문자열인 경우다.
        raw_tags = str(value).split(",")  # 쉼표를 기준으로 여러 태그를 나눈다.
    normalized: List[str] = []  # 정리가 끝난 태그를 담을 빈 목록을 만든다.
    for raw_tag in raw_tags:  # 입력 태그를 하나씩 확인한다.
        tag = raw_tag.strip()  # 현재 태그 앞뒤의 불필요한 공백을 제거한다.
        if tag and tag not in normalized:  # 빈 태그가 아니고 아직 추가하지 않은 태그인지 확인한다.
            normalized.append(tag)  # 조건을 만족한 태그만 결과에 추가한다.
    return normalized  # 정리가 끝난 태그 목록을 돌려준다.


def validate_optional_transaction_type(value: str) -> Optional[str]:  # 생략할 수 있는 거래 타입 입력을 검사한다.
    if value == "":  # 사용자가 아무것도 입력하지 않고 엔터를 눌렀는지 확인한다.
        return None  # 검색 조건 생략을 뜻하는 None을 돌려준다.
    return validate_transaction_type(value)  # 값이 있으면 일반 거래 타입 검증으로 넘긴다.
