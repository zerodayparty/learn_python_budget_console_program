# 이 파일은 사용자 입력이 요구사항에 맞는지 검사한다.

import re                                           # re는 문자열 모양을 검사하는 Regular Expression(정규 표현식) 도구다.
from datetime import datetime                       # datetime은 실제로 존재하는 날짜인지 검사하는 도구다.
from typing import List                             # List는 여러 문자열을 담는 목록의 타입을 표시한다.
from budget_app.constants import (  # 공통 상수 모듈에서 필요한 패턴과 포맷을 가져온다.
    ALLOWED_TYPES,  # 거래 타입 허용 목록('income', 'expense')을 가져온다.
    DATE_FORMAT,  # 날짜 형식 문자열('%Y-%m-%d')을 가져온다.
    DATE_PATTERN,  # 날짜 정규식 패턴을 가져온다.
    MONTH_FORMAT,  # 월 형식 문자열('%Y-%m')을 가져온다.
    MONTH_PATTERN,  # 월 정규식 패턴을 가져온다.
)  # 상수 가져오기를 끝낸다.
from budget_app.exceptions import ValidationError   # 입력 오류를 한 가지 형식으로 전달하기 위해 가져온다.


# ✅
def validate_date(value: str) -> str:                   # 날짜 문자열을 검사하고 올바른 값을 돌려준다.
    cleaned = value.strip()                             # 입력 앞뒤의 불필요한 공백을 제거한다.
    if not DATE_PATTERN.fullmatch(cleaned):             # 글자 모양이 YYYY-MM-DD가 아니면 오류로 처리한다.
        raise ValidationError("날짜 형식이 올바르지 않다.", "YYYY-MM-DD 형식으로 입력한다. 예: 2026-08-01")  # 원인과 해결법을 전달한다.
    try:  # 실제 달력에 존재하는 날짜인지 확인을 시도한다.
        datetime.strptime(cleaned, DATE_FORMAT)              # 문자열을 연도-월-일 날짜로 바꿔 본다.
    except ValueError as error:                             # 2월 30일처럼 존재하지 않는 날짜면 이 오류가 발생한다.
        message = "달력에 존재하지 않는 날짜다."                   # 사용자에게 보여 줄 날짜 오류 원인을 저장한다.
        hint = "실제로 존재하는 날짜를 입력한다. 예: 2026-02-28"    # 올바른 날짜 입력 예시를 저장한다.
        raise ValidationError(message, hint) from error     # 저장한 원인과 힌트로 입력 오류를 발생시킨다.
    return cleaned                                          # 모든 검사를 통과한 날짜를 돌려준다.


# ✅
def validate_month(value: str) -> str:                  # 월 문자열을 검사하고 올바른 값을 돌려준다.
    cleaned = value.strip()                             # 입력 앞뒤의 불필요한 공백을 제거한다.
    if not MONTH_PATTERN.fullmatch(cleaned):            # 글자 모양이 YYYY-MM이 아니면 오류로 처리한다.
        raise ValidationError("월 형식이 올바르지 않다.", "YYYY-MM 형식으로 입력한다. 예: 2026-08")  # 원인과 해결법을 전달한다.
    
    try:                                                # 01부터 12까지의 실제 월인지 확인을 시도한다.
        datetime.strptime(cleaned, MONTH_FORMAT)             # 문자열을 연도-월 값으로 바꿔 본다.
    
    except ValueError as error:                         # 13월처럼 존재하지 않는 월이면 이 오류가 발생한다.
        raise ValidationError("존재하지 않는 월이다.", "01부터 12 사이의 월을 입력한다.") from error  # 사용자용 오류로 바꾼다.
    return cleaned                                      # 모든 검사를 통과한 월을 돌려준다.


# ✅
def validate_amount(value: object) -> int:  # 금액을 양의 정수로 바꿔서 돌려준다.
    if isinstance(value, bool):  # True와 False는 Python에서 숫자로 취급되므로 먼저 막는다.
        raise ValidationError("금액은 숫자여야 한다.", "0보다 큰 정수를 입력한다. 예: 15000")  # 잘못된 자료형을 알린다.
    
    try:  # 🔥 입력을 정수로 바꾸는 작업을 시도한다.
        amount = int(str(value).strip())  # 문자열로 받은 금액을 정수로 변환한다.
    except (TypeError, ValueError) as error:  # 정수로 바꿀 수 없으면 이 오류가 발생한다.
        raise ValidationError("금액은 정수여야 한다.", "소수점 없이 0보다 큰 정수를 입력한다. 예: 15000") from error  # 사용자용 오류로 바꾼다.
    
    
    if amount <= 0:  # 금액이 0이거나 음수인지 검사한다.
        raise ValidationError("금액은 0보다 커야 한다.", "1 이상의 정수를 입력한다.")  # 양수 입력 방법을 알린다.
    
    return amount  # 검사한 양의 정수를 돌려준다.


# ✅
def validate_transaction_type(value: str) -> str:  # 거래 타입이 income 또는 expense인지 검사한다.
    cleaned = value.strip().lower()  # 대소문자 차이를 없애고 앞뒤 공백을 제거한다.
    if cleaned not in ALLOWED_TYPES:  # 허용 목록에 없는 값인지 검사한다.
        raise ValidationError("거래 타입이 올바르지 않다.", "수입은 income, 지출은 expense로 입력한다.")  # 허용 값을 알려 준다.
    
    return cleaned  # 검사한 거래 타입을 돌려준다.


# ✅
def validate_category_name(value: str) -> str:  # 카테고리 이름이 저장 가능한지 검사한다.
    cleaned = value.strip()  # 이름 앞뒤의 불필요한 공백을 제거한다.
    
    if not cleaned:  # 공백을 지운 뒤 아무 글자도 없는지 검사한다.
        raise ValidationError("카테고리 이름이 비어 있다.", "한 글자 이상의 이름을 입력한다. 예: food")  # 이름 입력 방법을 알린다.
    
    if len(cleaned) > 50:  # 이름이 지나치게 긴지 검사한다.
        raise ValidationError("카테고리 이름이 50자를 넘는다.", "50자 이하로 줄여서 입력한다.")  # 최대 길이를 알린다.
    
    if "\n" in cleaned or "\r" in cleaned:  # 줄바꿈 문자가 이름에 들어 있는지 검사한다.
        raise ValidationError("카테고리 이름에 줄바꿈이 들어 있다.", "한 줄로 된 이름을 입력한다.")  # 한 줄 입력 방법을 알린다.
    
    return cleaned  # 검사한 카테고리 이름을 돌려준다.


# ✅
def normalize_tags(value: object) -> List[str]:  # 태그를 중복 없는 문자열 목록으로 정리한다.
    if value is None:                       # 태그가 생략되었는지 검사한다.
        return []                           # 생략된 태그는 빈 목록으로 바꾼다.
    
    if isinstance(value, list):             # JSONL에서 읽은 값이 이미 목록인지 검사한다.
        raw_tags: List[str] = []            # 문자열로 바꾼 원본 태그를 담을 빈 목록을 만든다.
        for item in value:                  # 입력 목록의 태그 값을 하나씩 꺼낸다.
            text_item = str(item)           # 현재 태그 값을 문자열로 바꾼다.
            raw_tags.append(text_item)      # 문자열 태그를 원본 태그 목록에 추가한다.
    
    else:                                   # 콘솔이나 CSV에서 쉼표로 구분한 문자열을 받은 경우다.
        raw_tags = str(value).split(",")    # 쉼표를 기준으로 여러 태그를 나눈다.
    
    normalized: List[str] = []              # 정리가 끝난 태그를 차례대로 담을 빈 목록이다.
    
    for raw_tag in raw_tags:                # 입력받은 태그를 하나씩 검사한다.
        tag = raw_tag.strip()               # 각 태그 앞뒤의 불필요한 공백을 제거한다.
        if tag and tag not in normalized:   # 빈 태그가 아니고 아직 저장하지 않은 태그인지 검사한다.
            normalized.append(tag)          # 조건을 만족한 태그만 결과 목록에 추가한다.
    
    return normalized                       # 정리가 끝난 태그 목록을 돌려준다.



