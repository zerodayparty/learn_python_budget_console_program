# 이 파일은 프로그램 전체에서 오류가 발생했을 때 보여줄 원인(message)과 해결 힌트(hint)를 한곳에 모아둔다.

from typing import Tuple  # 메시지와 힌트를 (message, hint) 쌍으로 표현하기 위해 Tuple을 가져온다.


class ErrorMessages:  # 에러 메시지와 해결 힌트를 보관하는 전담 클래스다.
    # -------------------------------------------------------------------------
    # 1. 입력 검증 관련 오류 (validators.py)
    # -------------------------------------------------------------------------
    INVALID_DATE_FORMAT = ("날짜 형식이 올바르지 않다.", "YYYY-MM-DD 형식으로 입력한다. 예: 2026-08-01")  # 날짜 형식 오류다.
    DATE_NOT_IN_CALENDAR = ("달력에 존재하지 않는 날짜다.", "실제로 존재하는 날짜를 입력한다. 예: 2026-02-28")  # 존재하지 않는 날짜 오류다.
    INVALID_MONTH_FORMAT = ("월 형식이 올바르지 않다.", "YYYY-MM 형식으로 입력한다. 예: 2026-08")  # 월 형식 오류다.
    MONTH_NOT_IN_CALENDAR = ("존재하지 않는 월이다.", "01부터 12 사이의 월을 입력한다.")  # 존재하지 않는 월 오류다.
    AMOUNT_MUST_BE_NUMBER = ("금액은 숫자여야 한다.", "0보다 큰 정수를 입력한다. 예: 15000")  # 금액 자료형 오류다.
    AMOUNT_MUST_BE_INTEGER = ("금액은 정수여야 한다.", "소수점 없이 0보다 큰 정수를 입력한다. 예: 15000")  # 금액 정수 오류다.
    AMOUNT_MUST_BE_POSITIVE = ("금액은 0보다 커야 한다.", "1 이상의 정수를 입력한다.")  # 금액 양수 오류다.
    INVALID_TRANSACTION_TYPE = ("거래 타입이 올바르지 않다.", "수입은 income, 지출은 expense로 입력한다.")  # 거래 타입 오류다.
    CATEGORY_NAME_EMPTY = ("카테고리 이름이 비어 있다.", "한 글자 이상의 이름을 입력한다. 예: food")  # 카테고리 빈 문자열 오류다.
    CATEGORY_NAME_TOO_LONG = ("카테고리 이름이 50자를 넘는다.", "50자 이하로 줄여서 입력한다.")  # 카테고리 길이 초과 오류다.
    CATEGORY_NAME_HAS_NEWLINE = ("카테고리 이름에 줄바꿈이 들어 있다.", "한 줄로 된 이름을 입력한다.")  # 카테고리 줄바꿈 포함 오류다.

    # -------------------------------------------------------------------------
    # 2. 업무 규칙 서비스 관련 오류 (services.py)
    # -------------------------------------------------------------------------
    LIMIT_MUST_BE_POSITIVE = ("목록 개수는 0보다 커야 한다.", "--limit 뒤에 1 이상의 정수를 입력한다.")  # limit 양수 오류다.
    DATE_RANGE_REVERSED = ("시작 날짜가 종료 날짜보다 늦다.", "--from 날짜를 --to 날짜보다 같거나 이르게 입력한다.")  # 날짜 범위 역전 오류다.
    NO_FIELDS_TO_UPDATE = ("수정할 항목이 없다.", "--date, --type, --category, --amount, --memo, --tags 중 하나 이상 입력한다.")  # 수정 필드 누락 오류다.
    TOP_MUST_BE_POSITIVE = ("TOP 개수는 0보다 커야 한다.", "--top 뒤에 1 이상의 정수를 입력한다.")  # top 양수 오류다.
    EXPORT_CONDITION_REQUIRED = ("export 조건이 없다.", "--month 또는 --from과 --to를 입력한다.")  # 내보내기 조건 누락 오류다.
    EXPORT_DATE_RANGE_INCOMPLETE = ("기간 조건이 한쪽만 입력되었다.", "--from과 --to를 함께 입력한다.")  # 내보내기 범위 불완전 오류다.

    # -------------------------------------------------------------------------
    # 3. 데이터 저장소 파일 관련 오류 (repositories.py, models.py)
    # -------------------------------------------------------------------------
    FILE_ENCODING_ERROR = ("파일 인코딩 오류가 발생했다.", "파일을 UTF-8 JSONL 형식으로 수정하거나 백업으로 복구한다.")  # 인코딩 오류다.
    JSON_FORMAT_INVALID = ("JSON 형식이 아닌 줄이 있다.", "각 줄을 중괄호로 된 JSON 객체 한 개로 저장한다.")  # JSON 형식 오류다.
    CATEGORY_RECORD_INVALID = ("카테고리 파일의 데이터 형식이 올바르지 않다.", '각 줄을 {"name":"food"} 모양으로 수정한다.')  # 카테고리 레코드 형식 오류다.
    CATEGORY_DUPLICATE_IN_FILE = ("카테고리 파일에 중복된 이름이 있다.", "중복된 카테고리 줄을 하나만 남긴다.")  # 카테고리 파일 내 중복 오류다.
    BUDGET_MISSING_FIELDS = ("budgets.jsonl 파일에 필수 항목이 없다.", "각 줄에 month와 amount를 모두 넣는다.")  # 예산 필수 필드 누락 오류다.
    BUDGET_DUPLICATE_MONTH = ("budgets.jsonl 파일에 중복된 월이 있다.", "월별 예산을 한 줄만 남긴다.")  # 예산 월 중복 오류다.
    TRANSACTION_DATA_CORRUPTED = ("저장된 거래 데이터가 손상되었다.", "손상된 줄을 수정하거나 백업 파일로 복구한다.")  # 거래 데이터 파싱 오류다.

    # -------------------------------------------------------------------------
    # 4. CLI 터미널 및 대화형 모드 관련 오류 (cli/app.py, cli/prompt.py)
    # -------------------------------------------------------------------------
    TRANSACTION_ID_REQUIRED = ("거래 id가 필요하다.", "--id 옵션으로 수정할 거래를 지정한다.")  # CLI 거래 ID 누락 오류다.

    # -------------------------------------------------------------------------
    # 5. 동적 변수가 포함된 오류 생성 함수들 (정적 메서드)
    # -------------------------------------------------------------------------
    @staticmethod  # 인스턴스 생성 없이 바로 호출 가능한 정적 함수로 정의한다.
    def unregistered_category(category: str) -> Tuple[str, str]:  # 등록되지 않은 카테고리 안내문을 반환한다.
        return (f"등록되지 않은 카테고리다: {category}", "category list로 확인하거나 category add로 먼저 등록한다.")  # 완성된 쌍을 돌려준다.

    @staticmethod  # 인스턴스 생성 없이 바로 호출 가능한 정적 함수로 정의한다.
    def transaction_not_found(tx_id: str) -> Tuple[str, str]:  # 존재하지 않는 거래 안내문을 반환한다.
        return (f"id={tx_id} 거래가 없다.", "list 또는 search로 존재하는 id를 확인한다.")  # 완성된 쌍을 돌려준다.

    @staticmethod  # 인스턴스 생성 없이 바로 호출 가능한 정적 함수로 정의한다.
    def category_in_use(category: str) -> Tuple[str, str]:  # 사용 중인 카테고리 삭제 불가 안내문을 반환한다.
        return (f"거래에서 사용 중인 카테고리는 삭제할 수 없다: {category}", "해당 거래의 카테고리를 update로 바꾼 뒤 다시 삭제한다.")  # 완성된 쌍을 돌려준다.

    @staticmethod  # 인스턴스 생성 없이 바로 호출 가능한 정적 함수로 정의한다.
    def category_not_found(category: str) -> Tuple[str, str]:  # 존재하지 않는 카테고리 안내문을 반환한다.
        return (f"category={category} 카테고리가 없다.", "category list로 등록된 이름을 확인한다.")  # 완성된 쌍을 돌려준다.

    @staticmethod  # 인스턴스 생성 없이 바로 호출 가능한 정적 함수로 정의한다.
    def category_already_exists(name: str) -> Tuple[str, str]:  # 이미 존재하는 카테고리 중복 생성 안내문을 반환한다.
        return (f"이미 존재하는 카테고리 이름이다: {name}", "category list로 기존 이름을 확인한 뒤 다른 이름을 사용한다.")  # 완성된 쌍을 돌려준다.

    @staticmethod  # 인스턴스 생성 없이 바로 호출 가능한 정적 함수로 정의한다.
    def csv_missing_headers(missing_text: str) -> Tuple[str, str]:  # CSV 필수 헤더 누락 안내문을 반환한다.
        return (f"CSV 필수 헤더가 없다: {missing_text}", "date,type,category,amount 헤더를 포함한다.")  # 완성된 쌍을 돌려준다.

    @staticmethod  # 인스턴스 생성 없이 바로 호출 가능한 정적 함수로 정의한다.
    def unknown_command(command: str) -> Tuple[str, str]:  # 알 수 없는 명령어 안내문을 반환한다.
        return (f"알 수 없는 명령이다: {command}", "--help로 사용할 수 있는 명령을 확인한다.")  # 완성된 쌍을 돌려준다.

    @staticmethod  # 인스턴스 생성 없이 바로 호출 가능한 정적 함수로 정의한다.
    def prompt_transaction_not_found(tx_id: str) -> Tuple[str, str]:  # 프롬프트 입력 시 거래 없음 안내문을 반환한다.
        return (f"id '{tx_id}' 거래가 없다.", "list 명령으로 존재하는 거래 id를 확인한다.")  # 완성된 쌍을 돌려준다.
