# 이 파일은 날짜, 월, 날짜 범위 입력만 검사한다.

from datetime import datetime  # datetime은 문자열이 실제 달력 날짜인지 확인하는 Python 표준 도구다.
from typing import Optional  # Optional은 값이 없을 수도 있음을 표시한다.

from budget_app.constants import DATE_FORMAT, DATE_PATTERN, ErrorMessages, MONTH_FORMAT, MONTH_PATTERN  # 날짜와 월 검증 규칙 및 오류 메시지를 가져온다.
from budget_app.exceptions import ValidationError  # 올바르지 않은 날짜를 프로그램 입력 오류로 알리기 위해 가져온다.


def validate_date(value: str) -> str:  # 날짜 문자열을 검사하고 정리된 값을 돌려준다.
    cleaned = value.strip()  # 날짜 앞뒤의 불필요한 공백을 제거한다.
    if not DATE_PATTERN.fullmatch(cleaned):  # 날짜 글자 모양이 YYYY-MM-DD인지 확인한다.
        raise ValidationError(*ErrorMessages.INVALID_DATE_FORMAT)  # 날짜 형식 오류와 해결 힌트를 알린다.
    try:  # 실제 달력에 존재하는 날짜인지 변환을 시도한다.
        datetime.strptime(cleaned, DATE_FORMAT)  # 문자열을 연도-월-일 날짜로 바꿔 본다.
    except ValueError as error:  # 2월 30일처럼 존재하지 않는 날짜 오류를 잡는다.
        raise ValidationError(*ErrorMessages.DATE_NOT_IN_CALENDAR) from error  # 사용자용 날짜 오류로 바꿔 알린다.
    return cleaned  # 모든 검사를 통과한 날짜를 돌려준다.


def validate_month(value: str) -> str:  # 월 문자열을 검사하고 정리된 값을 돌려준다.
    cleaned = value.strip()  # 월 앞뒤의 불필요한 공백을 제거한다.
    if not MONTH_PATTERN.fullmatch(cleaned):  # 월 글자 모양이 YYYY-MM인지 확인한다.
        raise ValidationError(*ErrorMessages.INVALID_MONTH_FORMAT)  # 월 형식 오류와 해결 힌트를 알린다.
    try:  # 01부터 12까지의 실제 월인지 변환을 시도한다.
        datetime.strptime(cleaned, MONTH_FORMAT)  # 문자열을 연도-월 값으로 바꿔 본다.
    except ValueError as error:  # 13월처럼 존재하지 않는 월 오류를 잡는다.
        raise ValidationError(*ErrorMessages.MONTH_NOT_IN_CALENDAR) from error  # 사용자용 월 오류로 바꿔 알린다.
    return cleaned  # 모든 검사를 통과한 월을 돌려준다.


def validate_optional_date(value: str) -> Optional[str]:  # 생략할 수 있는 날짜 입력을 검사한다.
    if value == "":  # 사용자가 아무것도 입력하지 않고 엔터를 눌렀는지 확인한다.
        return None  # 검색 조건 생략을 뜻하는 None을 돌려준다.
    return validate_date(value)  # 값이 있으면 일반 날짜 검증으로 넘긴다.


def validate_date_range(date_from: Optional[str], date_to: Optional[str]) -> None:  # 시작 날짜와 종료 날짜 순서를 검사한다.
    if date_from and date_to and date_from > date_to:  # 두 날짜가 있고 시작일이 종료일보다 늦은지 확인한다.
        raise ValidationError(*ErrorMessages.DATE_RANGE_REVERSED)  # 날짜 범위 역전 오류를 알린다.
