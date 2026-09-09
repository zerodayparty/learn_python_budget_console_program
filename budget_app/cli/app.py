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
from budget_app.cli.parser import build_parser  # CLI 명령어 및 옵션 해석기 생성 함수를 가져온다.
from budget_app.constants import (  # 공통 상수 모듈에서 기본 폴더명과 에러 메시지를 가져온다.
    DEFAULT_DATA_DIR,  # 기본 데이터 저장 폴더 이름이다.
    ErrorMessages,  # 오류 메시지 및 해결 힌트 모음 클래스를 가져온다.
)  # 상수 가져오기를 끝낸다.
from budget_app.exceptions import ConflictError, NotFoundError, ValidationError  # 대화형 입력에서 오류를 보여 주고 다시 받을 때 사용한다.
from budget_app.models import MonthlySummary, Transaction  # 거래와 요약을 화면 형식으로 출력하기 위해 가져온다.
from budget_app.repositories import BudgetStore, CategoryStore, TransactionRepository  # 세 저장 파일을 준비할 저장소다.
from budget_app.services import BudgetService  # 실제 가계부 업무 규칙을 실행할 서비스다.
from budget_app.validators import validate_amount, validate_date, validate_transaction_type  # 대화형 입력을 즉시 검사할 함수다.


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
        if args.category_action == "exists":  # 카테고리 존재 확인 작업을 선택한 경우다.
            name = args.name  # 명령줄 옵션으로 받은 카테고리 이름을 우선 읽는다.
            if name is None or not name.strip():  # 옵션이 생략되었거나 공백인지 확인한다.
                name = input("확인할 카테고리명: ")  # 옵션이 없으면 대화형으로 이름을 받는다.
            if service.category_exists(name):  # 카테고리가 등록되어 있는지 확인한다.
                print(f"[확인 완료] category={name.strip()} (등록되어 있음)")  # 등록되어 있음을 알린다.
            else:  # 등록되어 있지 않은 경우다.
                print(f"[확인 완료] category={name.strip()} (등록되어 있지 않음)")  # 등록되어 있지 않음을 알린다.
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
                                                # 🔥 파이썬 * (언패킹 연산자) = 튜플로 받은 것을 언패킹하여 ValidationError로 전달한다.
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






# 🔥 main 실행
def main(argv: Optional[List[str]] = None) -> int:  # 터미널 또는 테스트에서 프로그램을 시작하는 진입 함수다.
    try:  # 최상단에서 키보드 중단 및 입력 종료 예외를 감싸 스택트레이스를 방지한다.
        tokens = sys.argv[1:] if argv is None else argv  # 인자가 없으면 실제 터미널 인자를 가져오고 있으면 전달받은 인자를 쓴다.
        
        # ✅ [대화형 콘솔 기반] 보통의 경우 이렇게 진입하게 된다.
        if not tokens:  # 터미널에 아무런 옵션이나 명령어 없이 실행된 경우다.
            return run_interactive_console(Path("data"))  # 🔥 기본 data 폴더로 대화형 콘솔 메뉴를 실행한다.
        
        # ❌ ✅ 오직 --data-dir 저장 폴더만 지정하고 하위 명령이 없는 경우다.
        # 이 경우에는 별로 테스트 폴더에 테스트 할 떄나 사용 할 것 같다.)
        if len(tokens) == 2 and tokens[0] == "--data-dir":  
            return run_interactive_console(Path(tokens[1]))  # 지정한 폴더로 대화형 콘솔 메뉴를 실행한다.
        
        # ❌ ✅ 명시적으로 대화형 콘솔 명령을 친 경우다. 
        # (이렇게 치는 경우가 없을 것 같다...)
        if len(tokens) == 1 and tokens[0] in ["interactive", "console", "repl"]:  
            return run_interactive_console(Path("data"))  # 기본 data 폴더로 대화형 콘솔 메뉴를 실행한다.
        
        # ✅ [옵션형 기반] 위 세가지 경우 외의 경우에는 '옵션형 기반'으로 작동된다.
        parser = build_parser()  # 모든 명령과 옵션이 등록된 해석기를 만든다.
        args = parser.parse_args(argv)  # 터미널 인자 또는 테스트 인자를 읽어 Namespace 객체로 바꾼다.
        return execute(args)  # 해석된 명령을 실행하고 종료 코드를 돌려준다.
    except (EOFError, KeyboardInterrupt):  # 최상위 레벨에서 잡힌 중단 예외를 처리한다.
        print("\n[오류] 사용자가 강제로 종료하여 프로그램이 중단되었습니다.")  # 프로그램이 중단된 원인을 출력한다.
        print("[힌트] 명령을 다시 실행하고 입력을 끝까지 완료한다.")  # 해결 힌트를 출력한다.
        return 130  # 사용자 중단 종료 코드를 돌려준다.
