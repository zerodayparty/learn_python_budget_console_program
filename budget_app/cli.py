# 이 파일은 터미널 명령어를 해석하고 서비스 결과를 화면에 출력한다.

import argparse  # argparse는 명령어와 --옵션을 해석하고 --help를 자동 생성한다.
from pathlib import Path  # Path는 사용자가 입력한 파일과 폴더 경로를 다루는 도구다.
from typing import Callable, List, Optional  # 함수의 입력과 출력 자료형을 표시한다.

from budget_app.decorators import handle_cli_errors  # 공통 오류 처리를 붙이는 데코레이터를 가져온다.
from budget_app.exceptions import ValidationError  # 대화형 입력에서 오류를 보여 주고 다시 받을 때 사용한다.
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
    parser.add_argument("--data-dir", default="data", help="저장 폴더 경로 (기본값: ./data)")  # 세 저장 파일을 둘 폴더를 바꿀 수 있게 한다.
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
    list_parser.add_argument("--limit", type=_positive_integer, default=10, help="출력할 최대 개수 (기본값: 10)")  # 최신 거래 출력 개수를 받는다.

    search_parser = commands.add_parser(  # search 명령 전용 해석기를 만든다.
        "search",  # 터미널에서 사용할 명령 이름을 search로 정한다.
        help="조건으로 거래 검색",  # 전체 도움말에 보일 짧은 설명을 정한다.
        description="입력한 모든 조건을 만족하는 거래를 최신순으로 찾는다.",  # search 도움말에 보일 상세 설명을 정한다.
    )  # search 명령 해석기 만들기를 끝낸다.
    search_parser.add_argument("--from", dest="date_from", help="시작 날짜 YYYY-MM-DD")  # 검색 시작 날짜를 받는다.
    search_parser.add_argument("--to", dest="date_to", help="종료 날짜 YYYY-MM-DD")  # 검색 종료 날짜를 받는다.
    search_parser.add_argument("--category", help="카테고리 이름")  # 검색 카테고리를 받는다.
    search_parser.add_argument("--type", dest="transaction_type", choices=["income", "expense"], help="거래 타입")  # 검색 거래 타입을 받는다.
    search_parser.add_argument("--q", dest="query", help="메모에 포함된 글자")  # 메모 검색어를 받는다.
    search_parser.add_argument("--tag", help="포함된 태그")  # 태그 조건을 받는다.

    summary_parser = commands.add_parser(  # summary 명령 전용 해석기를 만든다.
        "summary",  # 터미널에서 사용할 명령 이름을 summary로 정한다.
        help="월별 수입·지출 요약",  # 전체 도움말에 보일 짧은 설명을 정한다.
        description="월 합계와 지출 카테고리 TOP N을 계산한다.",  # summary 도움말에 보일 상세 설명을 정한다.
    )  # summary 명령 해석기 만들기를 끝낸다.
    summary_parser.add_argument("--month", required=True, help="계산할 월 YYYY-MM")  # 반드시 계산 대상 월을 받는다.
    summary_parser.add_argument("--top", type=_positive_integer, default=3, help="출력할 지출 카테고리 개수 (기본값: 3)")  # 상위 카테고리 개수를 받는다.

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

    update_parser = commands.add_parser(  # update 명령 전용 해석기를 만든다.
        "update",  # 터미널에서 사용할 명령 이름을 update로 정한다.
        help="id로 거래 수정",  # 전체 도움말에 보일 짧은 설명을 정한다.
        description="입력한 옵션의 필드만 수정하고 나머지는 유지한다.",  # update 도움말에 보일 상세 설명을 정한다.
    )  # update 명령 해석기 만들기를 끝낸다.
    update_parser.add_argument("--id", required=True, help="수정할 거래 id")  # 반드시 수정 대상 id를 받는다.
    update_parser.add_argument("--date", help="새 날짜 YYYY-MM-DD")  # 선택 수정 날짜를 받는다.
    update_parser.add_argument("--type", dest="transaction_type", choices=["income", "expense"], help="새 거래 타입")  # 선택 수정 타입을 받는다.
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


def _prompt_until_valid(label: str, validator: Callable[[str], object]) -> object:  # 올바른 값을 받을 때까지 대화형 입력을 반복한다.
    while True:  # 검사를 통과하거나 사용자가 입력을 중단할 때까지 반복한다.
        raw = input(label)  # 안내 문구를 출력하고 사용자의 한 줄 입력을 받는다.
        try:  # 현재 입력값 검사를 시도한다.
            return validator(raw)  # 검사를 통과한 값을 즉시 돌려주면서 반복을 끝낸다.
        except ValidationError as error:  # 사용자가 고칠 수 있는 입력 오류를 잡는다.
            print(f"[오류] {error.message}")  # 잘못된 이유를 스택트레이스 없이 출력한다.
            print(f"[힌트] {error.hint}")  # 올바르게 다시 입력하는 방법을 출력한다.


def _prompt_registered_category(service: BudgetService) -> str:  # 등록된 카테고리를 입력할 때까지 반복한다.
    while True:  # 등록된 이름을 받거나 사용자가 입력을 중단할 때까지 반복한다.
        category = input("카테고리: ").strip()  # 카테고리 이름을 받고 앞뒤 공백을 제거한다.
        if category in service.list_categories():  # 입력한 이름이 저장된 목록에 있는지 확인한다.
            return category  # 등록된 이름이면 즉시 돌려주면서 반복을 끝낸다.
        print("[오류] 등록되지 않은 카테고리다.")  # 존재하지 않는 이름임을 알린다.
        print("[힌트] 사용 가능: " + ", ".join(service.list_categories()))  # 지금 선택 가능한 이름을 보여 준다.


def _print_transaction(transaction: Transaction) -> None:  # 거래 한 건을 읽기 쉬운 한 줄로 출력한다.
    tags = ",".join(transaction.tags)  # 태그 목록을 쉼표로 이어 붙인 문자열로 만든다.
    columns = [  # 화면에 출력할 거래 값을 순서대로 담는다.
        transaction.id,  # 첫 번째 열에 거래 id를 넣는다.
        transaction.date,  # 두 번째 열에 거래 날짜를 넣는다.
        transaction.type,  # 세 번째 열에 거래 타입을 넣는다.
        transaction.category,  # 네 번째 열에 카테고리를 넣는다.
        str(transaction.amount),  # 다섯 번째 열에 문자열로 바꾼 금액을 넣는다.
        transaction.memo,  # 여섯 번째 열에 메모를 넣는다.
        tags,  # 일곱 번째 열에 쉼표로 연결한 태그를 넣는다.
    ]  # 거래 출력 열 만들기를 끝낸다.
    line = " | ".join(columns)  # 각 열 사이에 세로 구분선을 넣어 한 줄로 연결한다.
    print(line)  # 완성한 거래 한 줄을 화면에 출력한다.


def _print_summary(summary: MonthlySummary) -> None:  # 월별 계산 결과를 요구사항 순서로 출력한다.
    if summary.transaction_count == 0:  # 해당 월에 거래가 하나도 없는지 확인한다.
        print(f"{summary.month}: 데이터 없음")  # 데이터가 없다는 사실을 명확히 출력한다.
    else:  # 해당 월에 거래가 한 건 이상 있는 경우다.
        print(f"총 수입: {summary.total_income}원")  # 해당 월의 모든 수입 합계를 출력한다.
        print(f"총 지출: {summary.total_expense}원")  # 해당 월의 모든 지출 합계를 출력한다.
        print(f"잔액: {summary.balance}원")  # 총수입에서 총지출을 뺀 잔액을 출력한다.
    if summary.budget is not None:  # 해당 월에 예산이 설정되어 있는지 확인한다.
        print(f"예산: {summary.budget}원 (사용률 {summary.budget_usage:.1f}%)")  # 예산과 지출 사용률을 함께 출력한다.
        if summary.is_over_budget:  # 총지출이 예산보다 큰지 확인한다.
            print("[경고] 월 예산을 초과했다.")  # 예산 초과 경고 문구를 출력한다.
    if summary.transaction_count > 0 and summary.category_expenses:  # 거래와 지출 카테고리 합계가 모두 있는지 확인한다.
        print("지출 카테고리 TOP")  # 이어지는 목록의 뜻을 제목으로 출력한다.
        for rank, (category, amount) in enumerate(summary.category_expenses, start=1):  # 큰 금액부터 1위 번호를 붙여 읽는다.
            print(f"{rank}) {category} {amount}원")  # 순위, 카테고리, 합계를 한 줄로 출력한다.


def _build_service(data_dir: Path) -> BudgetService:  # 한 저장 폴더를 사용하는 서비스 객체를 만든다.
    transactions = TransactionRepository(data_dir)  # transactions.jsonl 파일을 만들고 거래 저장소를 준비한다.
    categories = CategoryStore(data_dir)  # categories.jsonl과 기본 카테고리를 준비한다.
    budgets = BudgetStore(data_dir)  # budgets.jsonl 파일을 만들고 예산 저장소를 준비한다.
    return BudgetService(transactions, categories, budgets)  # 세 저장소를 연결한 서비스 객체를 돌려준다.


@handle_cli_errors  # 아래 모든 명령에 스택트레이스 없는 공통 오류 처리를 실제 적용한다.
def execute(args: argparse.Namespace) -> int:  # argparse가 해석한 명령 한 개를 실행한다.
    service = _build_service(Path(args.data_dir))  # 선택한 저장 폴더로 세 파일과 서비스를 준비한다.
    if args.command == "add":  # 사용자가 add 명령을 선택했는지 확인한다.
        date = str(_prompt_until_valid("날짜(YYYY-MM-DD): ", validate_date))  # 올바른 날짜를 받을 때까지 반복한다.
        transaction_type = str(_prompt_until_valid("타입(income/expense): ", validate_transaction_type))  # 올바른 타입을 받을 때까지 반복한다.
        category = _prompt_registered_category(service)  # 등록된 카테고리를 받을 때까지 반복한다.
        amount = _prompt_until_valid("금액(양의 정수): ", validate_amount)  # 양의 정수 금액을 받을 때까지 반복한다.
        memo = input("메모(선택): ")  # 빈 값도 허용하는 메모를 한 줄 받는다.
        tags = input("태그(쉼표로 구분, 선택): ")  # 빈 값도 허용하는 태그 문자열을 한 줄 받는다.
        transaction = service.add_transaction(date, transaction_type, category, amount, memo, tags)  # 검증된 입력으로 거래를 저장한다.
        print(f"[저장 완료] id={transaction.id}")  # 저장 성공과 생성된 고유 id를 출력한다.
        return 0  # 정상 종료 코드를 돌려준다.
    if args.command == "list":  # 사용자가 list 명령을 선택했는지 확인한다.
        found = False  # 거래가 한 건이라도 출력됐는지 기억할 값을 거짓으로 시작한다.
        for transaction in service.list_transactions(args.limit):  # 결과를 목록에 모으지 않고 제너레이터에서 한 건씩 꺼낸다.
            found = True  # 출력할 거래를 찾았다고 표시한다.
            _print_transaction(transaction)  # 거래 한 건을 한 줄 형식으로 출력한다.
        if not found:  # 저장된 거래가 하나도 없어서 한 번도 출력하지 않았는지 확인한다.
            print("거래 데이터 없음")  # 빈 목록임을 명확히 출력한다.
        return 0  # 정상 종료 코드를 돌려준다.
    if args.command == "search":  # 사용자가 search 명령을 선택했는지 확인한다.
        found = False  # 검색 결과가 한 건이라도 출력됐는지 기억할 값을 거짓으로 시작한다.
        for transaction in service.search_transactions(  # 결과를 목록에 모으지 않고 검색 제너레이터에서 한 건씩 꺼낸다.
                date_from=args.date_from,  # 시작 날짜 조건을 전달한다.
                date_to=args.date_to,  # 종료 날짜 조건을 전달한다.
                category=args.category,  # 카테고리 조건을 전달한다.
                transaction_type=args.transaction_type,  # 거래 타입 조건을 전달한다.
                query=args.query,  # 메모 검색어 조건을 전달한다.
                tag=args.tag,  # 태그 조건을 전달한다.
        ):  # 검색 조건 전달을 끝내고 결과 반복을 시작한다.
            found = True  # 출력할 검색 결과를 찾았다고 표시한다.
            _print_transaction(transaction)  # 거래 한 건을 한 줄 형식으로 출력한다.
        if not found:  # 모든 거래를 검사했지만 조건을 만족한 결과가 없었는지 확인한다.
            print("검색 결과 없음")  # 빈 검색 결과임을 명확히 출력한다.
        return 0  # 정상 종료 코드를 돌려준다.
    if args.command == "summary":  # 사용자가 summary 명령을 선택했는지 확인한다.
        _print_summary(service.monthly_summary(args.month, args.top))  # 월별 계산을 실행하고 결과를 출력한다.
        return 0  # 정상 종료 코드를 돌려준다.
    if args.command == "budget" and args.budget_action == "set":  # 사용자가 budget set을 선택했는지 확인한다.
        amount = service.set_budget(args.month, args.amount)  # 월과 금액을 검사해서 예산 파일에 저장한다.
        print(f"[저장 완료] {args.month} 예산 {amount}원")  # 저장한 월과 예산 금액을 출력한다.
        return 0  # 정상 종료 코드를 돌려준다.
    if args.command == "budget" and args.budget_action == "get":  # 사용자가 budget get을 선택했는지 확인한다.
        amount = service.get_budget(args.month)  # 해당 월에 저장된 예산을 조회한다.
        if amount is None:  # 해당 월에 설정된 예산이 없는지 확인한다.
            print(f"{args.month}: 예산 설정 없음")  # 예산이 없다는 사실을 명확히 출력한다.
        else:  # 해당 월에 저장된 예산이 있는 경우다.
            print(f"{args.month}: 예산 {amount}원")  # 조회한 월과 금액을 출력한다.
        return 0  # 정상 종료 코드를 돌려준다.
    if args.command == "category" and args.category_action == "add":  # 사용자가 category add를 선택했는지 확인한다.
        name = args.name  # 먼저 --name 옵션으로 받은 값을 저장한다.
        if name is None:  # 사용자가 --name 옵션을 생략했는지 확인한다.
            name = input("카테고리명: ")  # 옵션이 없으면 대화형으로 카테고리 이름을 받는다.
        saved_name = service.add_category(name)  # 이름을 검사하고 카테고리 파일에 저장한다.
        print(f"[저장 완료] category={saved_name}")  # 저장한 카테고리 이름을 출력한다.
        return 0  # 정상 종료 코드를 돌려준다.
    if args.command == "category" and args.category_action == "list":  # 사용자가 category list를 선택했는지 확인한다.
        categories = service.list_categories()  # 정렬된 전체 카테고리 목록을 조회한다.
        if not categories:  # 저장된 카테고리가 하나도 없는지 확인한다.
            print("카테고리 없음")  # 빈 목록임을 명확히 출력한다.
        for category in categories:  # 카테고리를 한 개씩 꺼낸다.
            print(f"- {category}")  # 각 이름 앞에 목록 기호를 붙여 출력한다.
        return 0  # 정상 종료 코드를 돌려준다.
    if args.command == "category" and args.category_action == "remove":  # 사용자가 category remove를 선택했는지 확인한다.
        name = args.name  # 먼저 --name 옵션으로 받은 값을 저장한다.
        if name is None:  # 사용자가 --name 옵션을 생략했는지 확인한다.
            name = input("삭제할 카테고리명: ")  # 옵션이 없으면 대화형으로 삭제할 이름을 받는다.
        service.remove_category(name)  # 사용 중인지 확인하고 안전한 경우만 삭제한다.
        print(f"[삭제 완료] category={name.strip()}")  # 삭제한 카테고리 이름을 출력한다.
        return 0  # 정상 종료 코드를 돌려준다.
    if args.command == "update":  # 사용자가 update 명령을 선택했는지 확인한다.
        transaction = service.update_transaction(  # id를 찾고 전달된 필드만 검사해서 수정한다.
            transaction_id=args.id,  # 수정 대상 id를 전달한다.
            date=args.date,  # 선택 새 날짜를 전달한다.
            transaction_type=args.transaction_type,  # 선택 새 거래 타입을 전달한다.
            category=args.category,  # 선택 새 카테고리를 전달한다.
            amount=args.amount,  # 선택 새 금액을 전달한다.
            memo=args.memo,  # 선택 새 메모를 전달한다.
            tags=args.tags,  # 선택 새 태그를 전달한다.
        )  # 거래 수정 요청 전달을 끝낸다.
        print(f"[수정 완료] id={transaction.id}")  # 수정 성공과 거래 id를 출력한다.
        return 0  # 정상 종료 코드를 돌려준다.
    if args.command == "delete":  # 사용자가 delete 명령을 선택했는지 확인한다.
        service.delete_transaction(args.id)  # id가 같은 거래를 임시 파일 교체 방식으로 삭제한다.
        print(f"[삭제 완료] id={args.id}")  # 삭제 성공과 거래 id를 출력한다.
        return 0  # 정상 종료 코드를 돌려준다.
    if args.command == "import":  # 사용자가 import 명령을 선택했는지 확인한다.
        imported, skipped, errors = service.import_csv(Path(args.source))  # CSV를 읽고 저장 수와 건너뜀 이유를 받는다.
        for error in errors:  # 건너뛴 각 CSV 줄의 이유를 한 건씩 꺼낸다.
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
    message = "지원하지 않는 명령이다."  # 모든 분기에 없는 경우 보여 줄 오류 원인을 저장한다.
    hint = "--help로 사용할 수 있는 명령을 확인한다."  # 사용자가 명령 목록을 확인하는 해결 방법을 저장한다.
    raise ValidationError(message, hint)  # 저장한 원인과 힌트로 명확한 오류를 만든다.


def main(argv: Optional[List[str]] = None) -> int:  # 터미널 또는 테스트에서 프로그램을 시작하는 진입 함수다.
    parser = build_parser()  # 모든 명령과 옵션이 등록된 해석기를 만든다.
    args = parser.parse_args(argv)  # 터미널 인자 또는 테스트 인자를 읽어 Namespace 객체로 바꾼다.
    return execute(args)  # 해석된 명령을 실행하고 종료 코드를 돌려준다.
