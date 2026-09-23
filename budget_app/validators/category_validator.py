# 이 파일은 카테고리 이름 입력만 검사한다.

from typing import Optional  # Optional은 카테고리 입력이 생략될 수 있음을 표시한다.

from budget_app.constants import ErrorMessages  # 카테고리 입력 오류 메시지를 가져온다.
from budget_app.exceptions import ValidationError  # 잘못된 카테고리 입력을 같은 오류 형식으로 알리기 위해 가져온다.


def validate_category_name(value: str) -> str:  # 카테고리 이름이 저장 가능한지 검사한다.
    cleaned = value.strip()  # 이름 앞뒤의 불필요한 공백을 제거한다.
    if not cleaned:  # 공백을 지운 뒤 아무 글자도 없는지 확인한다.
        raise ValidationError(*ErrorMessages.CATEGORY_NAME_EMPTY)  # 빈 이름 오류를 알린다.
    if len(cleaned) > 50:  # 이름이 50자를 넘는지 확인한다.
        raise ValidationError(*ErrorMessages.CATEGORY_NAME_TOO_LONG)  # 이름 길이 초과 오류를 알린다.
    if "\n" in cleaned or "\r" in cleaned:  # 이름에 줄바꿈 문자가 들어 있는지 확인한다.
        raise ValidationError(*ErrorMessages.CATEGORY_NAME_HAS_NEWLINE)  # 줄바꿈 포함 오류를 알린다.
    return cleaned  # 검사를 통과한 카테고리 이름을 돌려준다.


def validate_optional_category_name(value: str) -> Optional[str]:  # 생략할 수 있는 카테고리 이름을 검사한다.
    if value == "":  # 사용자가 아무것도 입력하지 않고 엔터를 눌렀는지 확인한다.
        return None  # 검색 조건 생략을 뜻하는 None을 돌려준다.
    return validate_category_name(value)  # 값이 있으면 일반 카테고리 검증으로 넘긴다.
