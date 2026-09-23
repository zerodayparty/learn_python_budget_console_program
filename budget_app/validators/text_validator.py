# 이 파일은 생략 가능한 일반 문자열 입력만 검사한다.

from typing import Optional  # Optional은 문자열 입력이 생략될 수 있음을 표시한다.

from budget_app.exceptions import ValidationError  # 공백만 입력한 경우 사용자 입력 오류를 알리기 위해 가져온다.


def validate_optional_text(value: str, field_name: str = "입력값") -> Optional[str]:  # 생략 가능한 문자열에서 공백 전용 입력을 막는다.
    if value == "":  # 사용자가 아무것도 입력하지 않고 엔터를 눌렀는지 확인한다.
        return None  # 검색 조건 생략을 뜻하는 None을 돌려준다.
    cleaned = value.strip()  # 입력 앞뒤의 불필요한 공백을 제거한다.
    if not cleaned:  # 공백을 지운 뒤 아무 글자도 없는지 확인한다.
        raise ValidationError(f"{field_name}에 공백만 입력할 수 없다.", "검색할 글자를 입력하거나 생략하려면 엔터만 누른다.")  # 공백 전용 입력 오류와 해결 힌트를 알린다.
    return cleaned  # 공백이 정리된 문자열을 돌려준다.
