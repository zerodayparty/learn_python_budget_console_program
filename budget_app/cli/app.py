# 이 파일은 터미널 명령줄 옵션을 해석(argparse)하고 각 명령을 실행하는 CLI 애플리케이션 총괄 모듈이다.

import argparse  # argparse는 명령어와 --옵션을 해석하고 --help를 자동 생성한다.
import sys  # sys는 명령줄 인자 목록을 직접 확인하기 위해 가져온다.
from pathlib import Path  # Path는 사용자가 입력한 파일과 폴더 경로를 다루는 도구다.
from typing import Callable, List, Optional  # 함수의 입력과 출력 자료형을 표시한다.

from budget_app.cli.decorators import handle_cli_errors  # CLI 전용 공통 오류 처리 데코레이터를 가져온다.
from budget_app.cli.interactive import run_interactive_console  # 대화형 콘솔 메뉴 실행 함수를 가져온다.
from budget_app.cli.output import (  # 화면 출력 도구들을 가져온다.
    print_divider,  # 구분선 출력 함수다.
    print_error,  # 오류 및 힌트 출력 함수다.
    print_section_title,  # 작업 소제목 출력 함수다.
    print_success,  # 성공 완료 문구 출력 함수다.
    print_warning,  # 경고 문구 출력 함수다.
)  # 출력 도구 가져오기를 끝낸다.
from budget_app.cli.prompt import (  # 대화형 입력 함수들을 가져온다.
    prompt_registered_category,  # 등록된 카테고리 입력 함수다.
    prompt_until_valid,  # 검증 통과할 때까지 입력받는 함수다.
    prompt_update_interactive,  # 대화형 거래 수정 함수다.
)  # 입력 함수 가져오기를 끝낸다.
from budget_app.cli.views import (  # 화면 뷰 출력 함수들을 가져온다.
    print_interactive_header,  # 대화형 모드 환영 배너 출력 함수다.
    print_main_menu,  # 메인 메뉴판 출력 함수다.
    print_summary,  # 월별 요약 통계 출력 함수다.
    print_transaction,  # 거래 한 줄 출력 함수다.
)  # 화면 뷰 가져오기를 끝낸다.
from budget_app.constants import (  # 공통 상수 모듈에서 CLI 기본값과 에러 메시지를 가져온다.
    DEFAULT_DATA_DIR,  # 기본 데이터 저장 폴더 이름이다.
    DEFAULT_LIST_LIMIT,  # 목록 출력 시 기본 개수다.
    DEFAULT_SUMMARY_TOP,  # 요약 시 상위 카테고리 기본 개수다.
    ErrorMessages,  # 오류 메시지 및 해결 힌트 모음 클래스를 가져온다.
    TRANSACTION_TYPES,  # 거래 허용 타입 튜플이다.
)  # 상수 가져오기를 끝낸다.
from budget_app.exceptions import ConflictError, NotFoundError, ValidationError  # 대화형 입력에서 오류를 보여 주고 다시 받을 때 사용한다.
from budget_app.models import MonthlySummary, Transaction  # 거래와 요약을 화면 형식으로 출력하기 위해 가져온다.
from budget_app.repositories import BudgetStore, CategoryStore, TransactionRepository  # 세 저장 파일을 준비할 저장소다.
from budget_app.services import BudgetService  # 실제 가계부 업무 규칙을 실행할 서비스다.
from budget_app.validators import validate_amount, validate_date, validate_transaction_type  # 대화형 입력을 즉시 검사할 함수다.


def _positive_integer(value: str) -> int:  # argparse 옵션 값을 1 이상의 정수로 검사한다.
    try:  # 문자열을 정수로 바꾸는 작업을 시도한다.
        number = int(value)  # 터미널에서 받은 문자열을 정수로 변환한다.
    except ValueError as error:  # 정수로 바꿀 수 없는 글자면 이 오류가 발생한다.
        raise argparse.ArgumentTypeError("1 이상의 정수를 입력한다.") from error  # argparse가 사용법과 함께 오류를 출력하게 한다.
    if number <= 0:  # 변환한 숫자가 0 또는 음수인지 검사한다.
        raise argparse.ArgumentTypeError("1 이상의 정수를 입력한다.")  # argparse가 올바른 범위를 출력하게 한다.
    return number  # 검사를 통과한 양의 정수를 돌려준다.


def build_parser() -> argparse.ArgumentParser:  # 모든 명령과 --help 정보를 가진 해석기를 만든다.
    parser = argparse.ArgumentParser(  # 프로그램 최상위 명령어 해석기를 만든다.
        prog="python -m budget_app",  # --help 첫 줄에 실제 실행 명령을 표시한다.
        description="JSONL 파일 기반 가계부 콘솔 프로그램",  # 프로그램의 목적을 한 줄로 설명한다.
    )  # 최상위 해석기 만들기를 끝낸다.
    parser.add_argument("--data-dir", default=DEFAULT_DATA_DIR, help=f"저장 폴더 경로 (기본값: ./{DEFAULT_DATA_DIR})")  # 세 저장 파일을 둘 폴더를 바꿀 수 있게 한다.
    commands = parser.add_subparsers(dest="command", required=True, title="명령")  # 반드시 하나의 하위 명령을 선택하게 한다.

    commands.add_parser(  # add 명령과 add --help 설명을 등록한다.
        "add",  # 터미널에서 사용할 명령 이름을 add로 정한다.
        help="대화형으로 거래 한 건 추가",  # 전체 도움말에 보일 짧은 설명을 정한다.
        description="날짜부터 태그까지 차례로 입력해 거래를 추가한다.",  # add 도움말에 보일 상세 설명을 정한다.
    )  # add 명령 등록을 끝낸다.

    list_parser = commands.add_parser(  # list 명령 전용 해석기를 만든다.
        "list",  # 터미널에서 사용할 명령 이름을 list로 정한다.
        help="최신순 거래 목록",  # 전체 도움말에 보일 짧은 설명을 정한다.
        description="JSONL 파일 끝에서부터 거래를 한 줄씩 읽는다.",  # list 도움말에 보일 상세 설명을 정한다.
    )  # list 명령 해석기 만들기를 끝낸다.
    list_parser.add_argument("--limit", type=_positive_integer, default=DEFAULT_LIST_LIMIT, help=f"출력할 최대 개수 (기본값: {DEFAULT_LIST_LIMIT})")  # 최신 거래 출력 개수를 받는다.

    search_parser = commands.add_parser(  # search 명령 전용 해석기를 만든다.
        "search",  # 터미널에서 사용할 명령 이름을 search로 정한다.
        help="조건으로 거래 검색",  # 전체 도움말에 보일 짧은 설명을 정한다.
        description="입력한 모든 조건을 만족하는 거래를 최신순으로 찾는다.",  # search 도움말에 보일 상세 설명을 정한다.
    )  # search 명령 해석기 만들기를 끝낸다.
    search_parser.add_argument("--from", dest="date_from", help="시작 날짜 YYYY-MM-DD")  # 검색 시작 날짜를 받는다.
    search_parser.add_argument("--to", dest="date_to", help="종료 날짜 YYYY-MM-DD")  # 검색 종료 날짜를 받는다.
    search_parser.add_argument("--category", help="카테고리 이름")  # 검색 카테고리를 받는다.
    search_parser.add_argument("--type", dest="transaction_type", choices=list(TRANSACTION_TYPES), help="거래 타입")  # 검색 거래 타입을 받는다.
    search_parser.add_argument("--q", dest="query", help="메모에 포함된 글자")  # 메모 검색어를 받는다.
    search_parser.add_argument("--tag", help="포함된 태그")  # 태그 조건을 받는다.

    summary_parser = commands.add_parser(  # summary 명령 전용 해석기를 만든다.
        "summary",  # 터미널에서 사용할 명령 이름을 summary로 정한다.
        help="월별 수입·지출 요약",  # 전체 도움말에 보일 짧은 설명을 정한다.
        description="월 합계와 지출 카테고리 TOP N을 계산한다.",  # summary 도움말에 보일 상세 설명을 정한다.
    )  # summary 명령 해석기 만들기를 끝낸다.
    summary_parser.add_argument("--month", required=True, help="계산할 월 YYYY-MM")  # 반드시 계산 대상 월을 받는다.
    summary_parser.add_argument("--top", type=_positive_integer, default=DEFAULT_SUMMARY_TOP, help=f"출력할 지출 카테고리 개수 (기본값: {DEFAULT_SUMMARY_TOP})")  # 상위 카테고리 개수를 받는다.

    budget_parser = commands.add_parser(  # budget 명령 전용 해석기를 만든다.
        "budget",  # 터미널에서 사용할 명령 이름을 budget으로 정한다.
        help="월 예산 설정·조회",  # 전체 도움말에 보일 짧은 설명을 정한다.
        description="월별 예산을 budgets.jsonl에 저장하거나 조회한다.",  # budget 도움말에 보일 상세 설명을 정한다.
    )  # budget 명령 해석기 만들기를 끝낸다.
    budget_actions = budget_parser.add_subparsers(dest="budget_action", required=True, title="예산 작업")  # set 또는 get을 반드시 선택하게 한다.
    budget_set_parser = budget_actions.add_parser("set", help="월 예산 저장")  # budget set 명령 해석기를 만든다.
    budget_set_parser.add_argument("--month", required=True, help="예산 월 YYYY-MM")  # 예산을 저장할 월을 받는다.
    budget_set_parser.add_argument("--amount", required=True, help="0보다 큰 정수 예산")  # 저장할 예산 금액을 받는다.
    budget_get_parser = budget_actions.add_parser("get", help="월 예산 조회")  # budget get 명령 해석기를 만든다.
    budget_get_parser.add_argument("--month", required=True, help="조회할 월 YYYY-MM")  # 예산을 조회할 월을 받는다.

    category_parser = commands.add_parser(  # category 명령 전용 해석기를 만든다.
        "category",  # 터미널에서 사용할 명령 이름을 category로 정한다.
        help="카테고리 추가·목록·삭제",  # 전체 도움말에 보일 짧은 설명을 정한다.
        description="거래에서 사용할 카테고리를 관리한다.",  # category 도움말에 보일 상세 설명을 정한다.
    )  # category 명령 해석기 만들기를 끝낸다.
    category_actions = category_parser.add_subparsers(dest="category_action", required=True, title="카테고리 작업")  # add, list, remove 중 하나를 선택하게 한다.
    category_add_parser = category_actions.add_parser("add", help="카테고리 추가")  # category add 명령 해석기를 만든다.
    category_add_parser.add_argument("--name", help="이름이며 생략하면 대화형으로 입력")  # 옵션 또는 대화형으로 이름을 받는다.
    category_actions.add_parser("list", help="카테고리 목록")  # category list와 --help를 등록한다.
    category_remove_parser = category_actions.add_parser("remove", help="사용하지 않는 카테고리 삭제")  # category remove 명령 해석기를 만든다.
    category_remove_parser.add_argument("--name", help="이름이며 생략하면 대화형으로 입력")  # 옵션 또는 대화형으로 삭제할 이름을 받는다.

    commands.add_parser(  # interactive 명령 전용 해석기를 만든다.
        "interactive",  # 터미널에서 사용할 명령 이름을 interactive로 정한다.
        help="대화형 콘솔 메뉴 실행",  # 전체 도움말에 보일 짧은 설명을 정한다.
        description="종료할 때까지 메뉴를 계속 선택하는 대화형 콘솔로 진입한다.",  # interactive 도움말에 보일 상세 설명을 정한다.
    )  # interactive 명령 등록을 끝낸다.

    update_parser = commands.add_parser(  # update 명령 전용 해석기를 만든다.
        "update",  # 터미널에서 사용할 명령 이름을 update로 정한다.
        help="id로 거래 수정 (대화형 지원)",  # 전체 도움말에 보일 짧은 설명을 정한다.
        description="옵션을 생략하면 대화형으로 수정할 필드를 묻고 저장한다.",  # update 도움말에 보일 상세 설명을 정한다.
    )  # update 명령 해석기 만들기를 끝낸다.
    update_parser.add_argument("--id", required=False, help="수정할 거래 id (생략 시 대화형 입력)")  # 수정 대상 id를 받으며 생략 시 대화형으로 묻는다.
    update_parser.add_argument("--date", help="새 날짜 YYYY-MM-DD")  # 선택 수정 날짜를 받는다.
    update_parser.add_argument("--type", dest="transaction_type", choices=list(TRANSACTION_TYPES), help="새 거래 타입")  # 선택 수정 타입을 받는다.
    update_parser.add_argument("--category", help="새 카테고리")  # 선택 수정 카테고리를 받는다.
    update_parser.add_argument("--amount", help="새 양의 정수 금액")  # 선택 수정 금액을 받는다.
    update_parser.add_argument("--memo", help="새 메모이며 빈 문자열이면 삭제")  # 선택 수정 메모를 받는다.
    update_parser.add_argument("--tags", help="새 쉼표 구분 태그이며 빈 문자열이면 삭제")  # 선택 수정 태그를 받는다.

    delete_parser = commands.add_parser(  # delete 명령 전용 해석기를 만든다.
        "delete",  # 터미널에서 사용할 명령 이름을 delete로 정한다.
        help="id로 거래 삭제",  # 전체 도움말에 보일 짧은 설명을 정한다.
        description="임시 파일을 이용해 특정 거래를 안전하게 삭제한다.",  # delete 도움말에 보일 상세 설명을 정한다.
    )  # delete 명령 해석기 만들기를 끝낸다.
    delete_parser.add_argument("--id", required=True, help="삭제할 거래 id")  # 반드시 삭제 대상 id를 받는다.

    import_parser = commands.add_parser(  # import 명령 전용 해석기를 만든다.
        "import",  # 터미널에서 사용할 명령 이름을 import로 정한다.
        help="CSV 거래 가져오기",  # 전체 도움말에 보일 짧은 설명을 정한다.
        description="고정 CSV 스키마의 거래를 검사하면서 저장한다.",  # import 도움말에 보일 상세 설명을 정한다.
    )  # import 명령 해석기 만들기를 끝낸다.
    import_parser.add_argument("--from", dest="source", required=True, help="가져올 UTF-8 CSV 경로")  # 반드시 원본 CSV 파일 경로를 받는다.

    export_parser = commands.add_parser(  # export 명령 전용 해석기를 만든다.
        "export",  # 터미널에서 사용할 명령 이름을 export로 정한다.
        help="조건별 CSV 내보내기",  # 전체 도움말에 보일 짧은 설명을 정한다.
        description="월 또는 날짜 범위에 맞는 거래를 UTF-8 CSV로 저장한다.",  # export 도움말에 보일 상세 설명을 정한다.
    )  # export 명령 해석기 만들기를 끝낸다.
    export_parser.add_argument("--out", required=True, help="만들 CSV 파일 경로")  # 반드시 출력 CSV 경로를 받는다.
    export_parser.add_argument("--month", help="내보낼 월 YYYY-MM")  # 선택 월 조건을 받는다.
    export_parser.add_argument("--from", dest="date_from", help="시작 날짜 YYYY-MM-DD")  # 선택 시작 날짜를 받는다.
    export_parser.add_argument("--to", dest="date_to", help="종료 날짜 YYYY-MM-DD")  # 선택 종료 날짜를 받는다.

    return parser  # 모든 명령과 옵션이 등록된 해석기를 돌려준다.


# prompt.py 및 views.py 모듈 함수 호환용 별칭
_prompt_until_valid = prompt_until_valid  # 대화형 값 검증 입력 함수다.
_prompt_registered_category = prompt_registered_category  # 등록된 카테고리 입력 함수다.
_prompt_update_interactive = prompt_update_interactive  # 대화형 거래 수정 함수다.
_print_transaction = print_transaction  # 거래 한 줄 출력 뷰 함수다.
_print_summary = print_summary  # 월별 요약 통계 출력 뷰 함수다.


def _build_service(data_dir: Path) -> BudgetService:  # 한 저장 폴더를 사용하는 서비스 객체를 만든다.
    transactions = TransactionRepository(data_dir)  # transactions.jsonl 파일을 만들고 거래 저장소를 준비한다.
    categories = CategoryStore(data_dir)  # categories.jsonl과 기본 카테고리를 준비한다.
    budgets = BudgetStore(data_dir)  # budgets.jsonl 파일을 만들고 예산 저장소를 준비한다.
    return BudgetService(transactions, categories, budgets)  # 세 저장소를 연결한 서비스 객체를 돌려준다.


@handle_cli_errors  # 예상치 못한 오류가 터져도 스택트레이스를 감추고 [오류], [힌트]를 출력한다.
def execute(args: argparse.Namespace) -> int:  # argparse가 해석한 명령 한 개를 실행한다.
    service = _build_service(Path(args.data_dir))  # 사용자가 지정한 데이터 폴더로 세 저장소와 서비스를 준비한다.

    if args.command == "add":  # 사용자가 add 명령을 선택했는지 확인한다.
        date = str(_prompt_until_valid("날짜(YYYY-MM-DD): ", validate_date))  # 검사를 통과할 때까지 날짜 입력을 받는다.
        transaction_type = str(_prompt_until_valid("타입(income/expense): ", validate_transaction_type))  # 거래 타입을 받는다.
        category = _prompt_registered_category(service)  # 등록된 카테고리를 받을 때까지 묻는다.
        amount = _prompt_until_valid("금액(양의 정수): ", validate_amount)  # 0보다 큰 금액을 받을 때까지 묻는다.
        memo = input("메모(선택): ")  # 메모는 선택 사항이므로 그대로 받는다.
        tags = input("태그(쉼표로 구분, 선택): ")  # 태그 문자열도 그대로 받는다.
        created = service.add_transaction(date, transaction_type, category, amount, memo, tags)  # 거래를 서비스에 저장한다.
        print(f"[저장 완료] id={created.id}")  # 생성된 거래 id를 사용자에게 보여 준다.
        return 0  # 성공 종료 코드를 돌려준다.

    if args.command == "list":  # 사용자가 list 명령을 선택했는지 확인한다.
        found = False  # 거래가 한 건이라도 있었는지 기억할 표시를 준비한다.
        for transaction in service.list_transactions(args.limit):  # 제너레이터에서 거래를 한 건씩 꺼낸다.
            found = True  # 적어도 한 건을 찾았다고 표시한다.
            _print_transaction(transaction)  # 거래를 요구사항 형식으로 화면에 출력한다.
        if not found:  # 거래가 하나도 없었는지 확인한다.
            print("거래 데이터 없음")  # 데이터가 없다는 사실을 명확히 알린다.
        return 0  # 성공 종료 코드를 돌려준다.

    if args.command == "search":  # 사용자가 search 명령을 선택했는지 확인한다.
        found = False  # 검색 결과가 한 건이라도 있었는지 기억할 표시를 준비한다.
        for transaction in service.search_transactions(  # 모든 검색 조건을 서비스에 넘기고 제너레이터로 결과를 받는다.
            date_from=args.date_from,  # 시작 날짜 조건을 전달한다.
            date_to=args.date_to,  # 종료 날짜 조건을 전달한다.
            category=args.category,  # 카테고리 조건을 전달한다.
            transaction_type=args.transaction_type,  # 거래 타입 조건을 전달한다.
            query=args.query,  # 메모 검색어를 전달한다.
            tag=args.tag,  # 포함 태그를 전달한다.
        ):  # 결과를 한 건씩 순회한다.
            found = True  # 적어도 한 건을 찾았다고 표시한다.
            _print_transaction(transaction)  # 찾은 거래를 요구사항 형식으로 출력한다.
        if not found:  # 조건을 만족하는 거래가 없었는지 확인한다.
            print("검색 결과 없음")  # 검색 결과가 없음을 명확히 출력한다.
        return 0  # 성공 종료 코드를 돌려준다.

    if args.command == "summary":  # 사용자가 summary 명령을 선택했는지 확인한다.
        summary = service.monthly_summary(args.month, args.top)  # 월 합계와 상위 지출 카테고리를 계산한다.
        _print_summary(summary)  # 요약 결과를 요구사항 순서대로 출력한다.
        return 0  # 성공 종료 코드를 돌려준다.

    if args.command == "budget":  # 사용자가 budget 하위 명령을 선택했는지 확인한다.
        if args.budget_action == "set":  # 예산 저장 작업을 선택한 경우다.
            amount = service.set_budget(args.month, args.amount)  # 예산을 검사하고 budgets.jsonl에 쓴다.
            print(f"[저장 완료] {args.month} 예산 {amount}원")  # 저장된 결과를 사용자에게 알린다.
            return 0  # 성공 종료 코드를 돌려준다.
        if args.budget_action == "get":  # 예산 조회 작업을 선택한 경우다.
            amount = service.get_budget(args.month)  # 저장된 예산을 읽어 온다.
            if amount is None:  # 예산이 설정되지 않았는지 확인한다.
                print(f"{args.month}: 예산 설정 없음")  # 예산이 없다는 문구를 출력한다.
            else:  # 예산이 설정되어 있는 경우다.
                print(f"{args.month}: 예산 {amount}원")  # 설정된 예산 금액을 출력한다.
            return 0  # 성공 종료 코드를 돌려준다.

    if args.command == "category":  # 사용자가 category 하위 명령을 선택했는지 확인한다.
        if args.category_action == "add":  # 카테고리 추가 작업을 선택한 경우다.
            name = args.name  # 명령줄 옵션으로 받은 카테고리 이름을 우선 읽는다.
            if name is None or not name.strip():  # 옵션이 생략되었거나 공백인지 확인한다.
                name = input("추가할 카테고리명: ")  # 옵션이 없으면 대화형으로 이름을 받는다.
            saved = service.add_category(name)  # 새 카테고리를 검사하고 추가한다.
            print(f"[저장 완료] category={saved}")  # 추가된 카테고리 이름을 알린다.
            return 0  # 성공 종료 코드를 돌려준다.
        if args.category_action == "list":  # 카테고리 목록 작업을 선택한 경우다.
            for category in service.list_categories():  # 정렬된 카테고리를 하나씩 꺼낸다.
                print(f"- {category}")  # 카테고리 목록을 글머리기호와 함께 출력한다.
            return 0  # 성공 종료 코드를 돌려준다.
        if args.category_action == "remove":  # 카테고리 삭제 작업을 선택한 경우다.
            name = args.name  # 명령줄 옵션으로 받은 카테고리 이름을 우선 읽는다.
            if name is None or not name.strip():  # 옵션이 생략되었거나 공백인지 확인한다.
                name = input("삭제할 카테고리명: ")  # 옵션이 없으면 대화형으로 이름을 받는다.
            service.remove_category(name)  # 사용 여부를 검사하고 카테고리를 삭제한다.
            print(f"[삭제 완료] category={name.strip()}")  # 삭제 성공을 알린다.
            return 0  # 성공 종료 코드를 돌려준다.

    if args.command == "interactive":  # 사용자가 interactive 명령을 선택했는지 확인한다.
        return run_interactive_console(Path(args.data_dir))  # 대화형 콘솔을 실행한다.

    if args.command == "update":  # 사용자가 update 명령을 선택했는지 확인한다.
        has_field_options = any(  # 개별 수정 옵션이 하나라도 주어졌는지 검사한다.
            value is not None  # 값이 실제로 들어왔는지 확인한다.
            for value in [args.date, args.transaction_type, args.category, args.amount, args.memo, args.tags]  # 검사할 필드 목록이다.
        )  # 필드 옵션 포함 여부를 계산한다.
        if has_field_options:  # 명령어 옵션으로 직접 수정할 필드를 준 경우다.
            if not args.id:  # 명령줄 옵션 방식에서는 거래 id가 필수다.
                raise ValidationError(*ErrorMessages.TRANSACTION_ID_REQUIRED)  # id 누락 오류를 알린다.
            updated = service.update_transaction(  # 전달받은 옵션만 골라 거래를 수정한다.
                transaction_id=args.id,  # 대상 거래 id를 전달한다.
                date=args.date,  # 새 날짜를 전달한다.
                transaction_type=args.transaction_type,  # 새 타입을 전달한다.
                category=args.category,  # 새 카테고리를 전달한다.
                amount=args.amount,  # 새 금액을 전달한다.
                memo=args.memo,  # 새 메모를 전달한다.
                tags=args.tags,  # 새 태그를 전달한다.
            )  # 수정 실행 결과를 받는다.
        else:  # 수정할 필드 옵션을 생략해서 대화형 수정을 원하는 경우다.
            updated = _prompt_update_interactive(service, transaction_id=args.id)  # 대화형으로 필드를 묻고 수정한다.
        print(f"[수정 완료] id={updated.id}")  # 수정된 거래 id를 알린다.
        return 0  # 성공 종료 코드를 돌려준다.

    if args.command == "delete":  # 사용자가 delete 명령을 선택했는지 확인한다.
        service.delete_transaction(args.id)  # 거래를 찾아 삭제하고 나머지 거래를 다시 쓴다.
        print(f"[삭제 완료] id={args.id}")  # 삭제된 거래 id를 알린다.
        return 0  # 성공 종료 코드를 돌려준다.

    if args.command == "import":  # 사용자가 import 명령을 선택했는지 확인한다.
        imported, skipped, errors = service.import_csv(Path(args.source))  # CSV 파일을 읽어 거래를 추가한다.
        for error in errors:  # 건너뛴 줄의 오류 원인을 하나씩 꺼낸다.
            print(f"[건너뜀] {error}")  # 줄 번호와 잘못된 이유를 출력한다.
        print(f"[완료] imported={imported}, skipped={skipped}")  # 최종 처리 건수를 요구사항 형식으로 출력한다.
        return 0  # 파일 전체 처리가 끝났으므로 정상 종료 코드를 돌려준다.

    if args.command == "export":  # 사용자가 export 명령을 선택했는지 확인한다.
        exported = service.export_csv(  # 조건에 맞는 거래를 CSV로 저장하고 개수를 받는다.
            output=Path(args.out),  # 만들 CSV 파일 경로를 전달한다.
            month=args.month,  # 선택 월 조건을 전달한다.
            date_from=args.date_from,  # 선택 시작 날짜 조건을 전달한다.
            date_to=args.date_to,  # 선택 종료 날짜 조건을 전달한다.
        )  # CSV 내보내기 요청 전달을 끝낸다.
        print(f"[완료] {args.out} ({exported} records)")  # 파일 경로와 처리 건수를 출력한다.
        return 0  # 정상 종료 코드를 돌려준다.

    raise ValidationError(*ErrorMessages.unknown_command(args.command))  # 지원하지 않는 명령 오류를 발생시킨다.


def main(argv: Optional[List[str]] = None) -> int:  # 터미널 또는 테스트에서 프로그램을 시작하는 진입 함수다.
    tokens = sys.argv[1:] if argv is None else argv  # 인자가 없으면 실제 터미널 인자를 가져오고 있으면 전달받은 인자를 쓴다.
    if not tokens:  # 터미널에 아무런 옵션이나 명령어 없이 실행된 경우다.
        return run_interactive_console(Path("data"))  # 기본 data 폴더로 대화형 콘솔 메뉴를 실행한다.
    if len(tokens) == 2 and tokens[0] == "--data-dir":  # 오직 --data-dir 저장 폴더만 지정하고 하위 명령이 없는 경우다.
        return run_interactive_console(Path(tokens[1]))  # 지정한 폴더로 대화형 콘솔 메뉴를 실행한다.
    if len(tokens) == 1 and tokens[0] in ["interactive", "console", "repl"]:  # 명시적으로 대화형 콘솔 명령을 친 경우다.
        return run_interactive_console(Path("data"))  # 기본 data 폴더로 대화형 콘솔 메뉴를 실행한다.
    parser = build_parser()  # 모든 명령과 옵션이 등록된 해석기를 만든다.
    args = parser.parse_args(argv)  # 터미널 인자 또는 테스트 인자를 읽어 Namespace 객체로 바꾼다.
    return execute(args)  # 해석된 명령을 실행하고 종료 코드를 돌려준다.
