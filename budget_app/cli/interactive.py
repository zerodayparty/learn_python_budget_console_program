# 이 파일은 사용자가 프로그램을 종료할 때까지 화면에 메뉴를 띄우고 작업을 이어가는 대화형 콘솔(TUI)을 담당한다.

from pathlib import Path  # 가계부 데이터가 저장된 폴더 경로를 다루기 위해 가져온다.
from typing import Optional  # 값이 없거나(None) 있을 수 있는 타입을 표시하기 위해 가져온다.

from budget_app.cli.output import print_error, print_section_title  # CLI 전용 표준 출력 도구들을 가져온다.
from budget_app.cli.prompt import (  # 사용자 대화형 입력을 유도하는 함수들을 가져온다.
    prompt_optional_valid,  # 생략 가능한 입력값 검증 도우미 함수다.
    prompt_registered_category,  # 등록된 카테고리만 입력받는 함수다.
    prompt_until_valid,  # 검증을 통과할 때까지 반복 입력받는 함수다.
    prompt_update_interactive,  # 거래 수정 필드를 하나씩 대화형으로 묻는 함수다.
)  # 대화형 입력 함수 가져오기를 마친다.
from budget_app.cli.views import (  # 화면에 데이터를 꾸며서 보여주는 뷰 함수들을 가져온다.
    print_interactive_header,  # 대화형 모드 환영 배너 출력 함수다.
    print_main_menu,  # 1~9번 메인 메뉴판 출력 함수다.
    print_summary,  # 월별 요약 통계 출력 함수다.
    print_transaction,  # 거래 한 줄 출력 함수다.
)  # 뷰 함수 가져오기를 마친다.
from budget_app.constants import DEFAULT_LIST_LIMIT, DEFAULT_SUMMARY_TOP, ErrorMessages  # 기본 출력 개수와 에러 메시지 상수를 가져온다.
from budget_app.exceptions import ConflictError, NotFoundError, ValidationError  # 대화형 메뉴에서 잡을 비즈니스 에러들을 가져온다.
from budget_app.repositories import BudgetStore, CategoryStore, TransactionRepository  # 저장 파일 3개를 다루는 저장소들을 가져온다.
from budget_app.services import BudgetService  # 가계부 핵심 계산 및 저장 규칙을 실행할 서비스를 가져온다.
from budget_app.validators import (  # 입력값 검증 함수들을 가져온다.
    validate_amount,  # 금액 검증 함수다.
    validate_category_name,  # 카테고리 이름 검증 함수다.
    validate_date,  # 날짜 검증 함수다.
    validate_date_range,  # 날짜 순서 검증 함수다.
    validate_month,  # 월 형식(YYYY-MM) 검증 함수다.
    validate_optional_category_name,  # 선택적 카테고리 검증 함수다.
    validate_optional_date,  # 선택적 날짜 검증 함수다.
    validate_optional_text,  # 선택적 텍스트 공백 검증 함수다.
    validate_optional_transaction_type,  # 선택적 거래 타입 검증 함수다.
    validate_transaction_type,  # 거래 타입 검증 함수다.
)  # 검증 함수 가져오기를 마친다.


def _build_service(data_dir: Path) -> BudgetService:  # 지정된 데이터 폴더의 저장소들을 조립해 서비스 객체를 만든다.
    transactions = TransactionRepository(data_dir)  # transactions.jsonl 파일 저장소를 준비한다.
    categories = CategoryStore(data_dir)  # categories.jsonl 파일 저장소를 준비한다.
    budgets = BudgetStore(data_dir)  # budgets.jsonl 파일 저장소를 준비한다.
    return BudgetService(transactions, categories, budgets)  # 세 저장소를 연결한 서비스 객체를 돌려준다.


def run_interactive_console(data_dir: Path) -> int:  # 사용자가 메뉴를 선택하며 계속 작업하는 대화형 콘솔을 실행한다.
    service = _build_service(data_dir)  # 지정된 데이터 폴더로 세 파일과 서비스를 초기화한다.

    print_interactive_header()  # views 모듈에서 대화형 모드 환영 배너를 화면에 출력한다.

    while True:  # 사용자가 종료를 선택할 때까지 메뉴 루프를 무한 반복한다.
        print_main_menu()  # views 모듈에서 1~9번 및 종료 메뉴 목록을 화면에 출력한다.

        try:  # 사용자 입력을 안전하게 받기 위한 예외 감지 블록을 연다.
            choice = input("\n메뉴 번호를 선택한다: ").strip().lower()  # 사용자로부터 원하는 메뉴 번호를 입력받는다.

        except (EOFError, KeyboardInterrupt):  # Ctrl+D 또는 Ctrl+C 등의 강제 종료 신호가 들어왔는지 확인한다.
            print("\n[강제종료 대응] 사용자의 강제종료로 인해 프로그램이 종료되었습니다.")  # 종료 안내 문구를 출력한다.
            return 0  # 정상 종료 코드를 돌려준다.

        if choice in ["q", "quit", "exit"]:  # 사용자가 종료 메뉴를 선택했는지 확인한다.
            print("🔚 가계부 프로그램을 종료한다. 👋 안녕히 가세요!")  # 친절한 종료 인사를 출력한다.
            return 0  # 정상 종료 코드를 돌려준다.

        try:  # 선택한 기능 실행 중 오류가 나도 메뉴판으로 안전하게 돌아오기 위한 감지 블록을 연다.

            if choice == "1":  # 1번 거래 추가를 선택한 경우다.
                print_section_title("거래 추가")  # 작업 소제목을 출력한다.
                date = str(prompt_until_valid("날짜(YYYY-MM-DD): ", validate_date))  # 날짜를 대화형으로 받는다.
                transaction_type = str(prompt_until_valid("타입(income/expense): ", validate_transaction_type))  # 타입을 대화형으로 받는다.
                category = prompt_registered_category(service)  # 등록된 카테고리를 대화형으로 받는다.
                amount = prompt_until_valid("금액(양의 정수): ", validate_amount)  # 금액을 대화형으로 받는다.
                memo = input("메모(선택): ")  # 메모를 대화형으로 받는다.
                tags = input("태그(쉼표로 구분, 선택): ")  # 태그를 대화형으로 받는다.
                tx = service.add_transaction(date, transaction_type, category, amount, memo, tags)  # 거래를 서비스에 저장한다.
                print(f"[저장 완료] id={tx.id}")  # 성공 메시지와 거래 고유 id를 출력한다.

            elif choice == "2":  # 2번 거래 목록 조회를 선택한 경우다.
                print_section_title("최근 거래 목록")  # 작업 소제목을 출력한다.
                raw_limit = input(f"출력 개수 (기본값: {DEFAULT_LIST_LIMIT}, 엔터 시 {DEFAULT_LIST_LIMIT}): ").strip()  # 출력 개수를 묻는다.
                limit = int(raw_limit) if raw_limit.isdigit() and int(raw_limit) > 0 else DEFAULT_LIST_LIMIT  # 숫자가 아니면 기본값을 사용한다.
                found = False  # 거래 출력 여부 플래그를 준비한다.
                for tx in service.list_transactions(limit):  # 제너레이터에서 거래를 하나씩 꺼낸다.
                    found = True  # 거래가 존재함을 표시한다.
                    print_transaction(tx)  # 거래 정보를 출력한다.
                if not found:  # 거래가 하나도 없었는지 확인한다.
                    print("❌ ⚠️ 거래 데이터 없음")  # 데이터 없음 안내를 출력한다.

            elif choice == "3":  # 3번 조건별 검색을 선택한 경우다.
                print_section_title("조건별 거래 검색 (생략하려면 엔터를 누른다)")  # 작업 소제목을 출력한다.
                raw_from = prompt_optional_valid("시작 날짜(YYYY-MM-DD): ", validate_optional_date)  # 시작 날짜를 별도 검증기로 받는다.
                q_date_from = str(raw_from) if raw_from is not None else None  # 문자열 또는 None으로 정제한다.

                def _validate_optional_date_to(value: str) -> Optional[str]:  # 종료 날짜 유효성과 시작일 비교를 함께 검사한다.
                    checked = validate_optional_date(value)  # 종료 날짜를 전용 검증기로 검사한다.
                    validate_date_range(q_date_from, checked)  # 시작 날짜와 종료 날짜 순서를 검사한다.
                    return checked  # 검증을 통과한 종료 날짜를 돌려준다.

                raw_to = prompt_optional_valid("종료 날짜(YYYY-MM-DD): ", _validate_optional_date_to)  # 종료 날짜를 검사하며 받는다.
                q_date_to = str(raw_to) if raw_to is not None else None  # 문자열 또는 None으로 정제한다.
                raw_cat = prompt_optional_valid("카테고리: ", validate_optional_category_name)  # 카테고리를 전용 검증기로 검사하며 받는다.
                q_category = str(raw_cat) if raw_cat is not None else None  # 문자열 또는 None으로 정제한다.
                raw_type = prompt_optional_valid("거래 타입(income/expense): ", validate_optional_transaction_type)  # 거래 타입을 전용 검증기로 검사하며 받는다.
                q_type = str(raw_type) if raw_type is not None else None  # 문자열 또는 None으로 정제한다.

                def _validate_memo(value: str) -> Optional[str]:  # 메모 검색어 공백 입력을 검사한다.
                    return validate_optional_text(value, "메모 검색어")  # 공백 검증 함수를 호출한다.

                def _validate_tag(value: str) -> Optional[str]:  # 태그 검색어 공백 입력을 검사한다.
                    return validate_optional_text(value, "포함 태그")  # 공백 검증 함수를 호출한다.

                raw_memo = prompt_optional_valid("메모 검색어: ", _validate_memo)  # 메모 검색어를 검사하며 받는다.
                q_memo = str(raw_memo) if raw_memo is not None else None  # 문자열 또는 None으로 정제한다.
                raw_tag = prompt_optional_valid("포함 태그: ", _validate_tag)  # 포함 태그를 검사하며 받는다.
                q_tag = str(raw_tag) if raw_tag is not None else None  # 문자열 또는 None으로 정제한다.
                found = False  # 검색 결과 여부 플래그를 준비한다.
                for tx in service.search_transactions(date_from=q_date_from, date_to=q_date_to, category=q_category, transaction_type=q_type, query=q_memo, tag=q_tag):  # 검색 제너레이터를 순회한다.
                    found = True  # 검색 결과가 있음을 표시한다.
                    print_transaction(tx)  # 거래를 출력한다.
                if not found:  # 검색 결과가 없는지 확인한다.
                    print("❌ ⚠️ 검색 결과 없음")  # 검색 결과 없음 문구를 출력한다.

            elif choice == "4":  # 4번 거래 수정을 선택한 경우다.
                print_section_title("거래 수정 (대화형)")  # 작업 소제목을 출력한다.
                tx = prompt_update_interactive(service)  # 대화형 프롬프트 함수를 호출한다.
                print(f"[수정 완료] id={tx.id}")  # 수정 성공 메시지를 출력한다.

            elif choice == "5":  # 5번 거래 삭제를 선택한 경우다.
                print_section_title("거래 삭제")  # 작업 소제목을 출력한다.
                print("[최근 거래 목록 (최대 10개)]")  # 삭제할 거래 선택을 돕기 위해 최신순 최대 10건의 목록을 먼저 출력한다.
                has_tx = False  # 거래 데이터 존재 여부를 기록할 플래그다.
                for tx in service.list_transactions(DEFAULT_LIST_LIMIT):  # 최신 거래를 최대 10개까지 한 건씩 꺼낸다.
                    has_tx = True  # 거래가 존재함을 표시한다.
                    print_transaction(tx)  # 거래 정보를 한 줄로 출력한다.
                if not has_tx:  # 등록된 거래가 하나도 없는 경우다.
                    print("❌ ⚠️ 거래 데이터 없음")  # 거래 데이터 없음 안내 문구를 출력한다.
                target_id = input("삭제할 거래 id: ").strip()  # 삭제할 id를 받는다.
                if target_id:  # id가 입력되었는지 확인한다.
                    service.delete_transaction(target_id)  # 안전하게 거래를 삭제한다.
                    print(f"[삭제 완료] id={target_id}")  # 삭제 완료 메시지를 출력한다.
                else:  # id가 비어 있는 경우다.
                    print_error("❌ ⚠️ 삭제할 거래 id를 입력해야 한다.")  # 안내를 출력한다.

            elif choice == "6":  # 6번 월별 요약을 선택한 경우다.
                print_section_title("월별 요약 및 예산")  # 작업 소제목을 출력한다.
                month = input("조회할 월(YYYY-MM): ").strip()  # 조회할 월을 받는다.
                if month:  # 월이 입력되었는지 확인한다.
                    raw_top = input(f"지출 상위 카테고리 개수 (기본값: {DEFAULT_SUMMARY_TOP}): ").strip()  # 상위 개수를 받는다.
                    top = int(raw_top) if raw_top.isdigit() and int(raw_top) > 0 else DEFAULT_SUMMARY_TOP  # 기본값을 정한다.
                    print_summary(service.monthly_summary(month, top))  # 요약을 출력한다.
                else:  # 월이 비어 있는 경우다.
                    print_error("❌ ⚠️ 조회할 월(YYYY-MM)을 입력해야 한다.")  # 안내를 출력한다.

            elif choice == "7":  # 7번 예산 관리를 선택한 경우다.
                print_section_title("월 예산 관리")  # 작업 소제목을 출력한다.
                print("<작업 선택>\n 1. 예산 설정(set)\n 2. 예산 조회(get)")  # 예산 관리 서브 메뉴 목록을 출력한다.
                b_action = input("선택: ").strip().lower()  # 서브 작업 번호나 영문 이름을 입력받는다.
                if b_action in ["1", "set"]:  # 예산 설정을 선택한 경우다.
                    b_month = str(prompt_until_valid("대상 월(YYYY-MM): ", validate_month))  # 올바른 대상 월을 입력받을 때까지 즉시 검증한다.
                    b_amount = prompt_until_valid("설정할 예산 금액: ", validate_amount)  # 올바른 예산 금액을 입력받을 때까지 즉시 검증한다.
                    saved_amt = service.set_budget(b_month, b_amount)  # 예산을 저장한다.
                    print(f"[저장 완료] {b_month} 예산 {saved_amt}원")  # 완료 메시지를 출력한다.
                elif b_action in ["2", "get"]:  # 예산 조회를 선택한 경우다.
                    b_month = str(prompt_until_valid("대상 월(YYYY-MM): ", validate_month))  # 올바른 대상 월을 입력받을 때까지 즉시 검증한다.
                    saved_amt = service.get_budget(b_month)  # 예산을 조회한다.
                    if saved_amt is None:  # 저장된 예산이 없는지 확인한다.
                        print(f"{b_month}: 예산 설정 없음")  # 없음 메시지를 출력한다.
                    else:  # 저장된 예산이 있는 경우다.
                        print(f"{b_month}: 예산 {saved_amt}원")  # 조회 결과를 출력한다.
                else:  # 잘못된 번호를 누른 경우다.
                    print("❌ ⚠️ 잘못된 선택이다.")  # 안내를 출력한다.

            elif choice == "8":  # 8번 카테고리 관리를 선택한 경우다.
                print_section_title("카테고리 관리")  # 작업 소제목을 출력한다.
                print("<작업 선택>\n 1. 카테고리 목록 출력(list)\n 2. 포함 여부(exists)\n 3. 카테고리 추가(add)\n 4. 카테고리 삭제(remove)")  # 카테고리 관리 서브 메뉴 목록을 출력한다.
                c_action = input("선택: ").strip().lower()  # 서브 작업 번호나 영문 이름을 입력받는다.
                if c_action in ["1", "list"]:  # 1번 목록 조회를 선택한 경우다.
                    cats = service.list_categories()  # 저장된 모든 카테고리 목록을 가져온다.
                    for c in cats:  # 카테고리 이름을 하나씩 순회한다.
                        print(f"- {c}")  # 카테고리 이름을 글머리기호와 함께 출력한다.
                elif c_action in ["2", "exists"]:  # 2번 포함 여부 확인을 선택한 경우다.
                    c_name = input("확인할 카테고리명: ").strip()  # 확인할 카테고리 이름을 입력받는다.
                    if service.category_exists(c_name):  # 특정 카테고리가 등록되어 있는지 확인한다.
                        print(f"[확인 완료] category={c_name} (등록되어 있음)")  # 등록되어 있음을 출력한다.
                    else:  # 등록되어 있지 않은 경우다.
                        print(f"[확인 완료] category={c_name} (등록되어 있지 않음)")  # 미등록 상태임을 출력한다.
                elif c_action in ["3", "add"]:  # 3번 카테고리 추가를 선택한 경우다.
                    c_name = input("추가할 카테고리명: ").strip()  # 새 카테고리 이름을 입력받는다.
                    saved = service.add_category(c_name)  # 새 카테고리를 검사하고 저장한다.
                    print(f"[저장 완료] category={saved}")  # 저장 완료 메시지를 출력한다.
                elif c_action in ["4", "remove"]:  # 4번 카테고리 삭제를 선택한 경우다.
                    c_name = input("삭제할 카테고리명: ").strip()  # 삭제할 카테고리 이름을 입력받는다.
                    service.remove_category(c_name)  # 사용 중 여부를 확인하고 카테고리를 삭제한다.
                    print(f"[삭제 완료] category={c_name}")  # 삭제 완료 메시지를 출력한다.
                else:  # 메뉴에 없는 값을 누른 경우다.
                    print("❌ ⚠️ 잘못된 선택이다.")  # 올바른 선택 안내를 출력한다.

            elif choice == "9":  # 9번 CSV 관리를 선택한 경우다.
                print_section_title("CSV 파일 처리")  # 작업 소제목을 출력한다.
                print("<작업 선택>\n 1. 가져오기(import)\n 2. 내보내기(export)")  # CSV 처리 서브 메뉴 목록을 출력한다.
                csv_action = input("선택: ").strip().lower()  # 서브 작업 번호나 영문 이름을 입력받는다.
                if csv_action in ["1", "import"]:  # 가져오기를 선택한 경우다.
                    csv_source = input("가져올 CSV 파일 경로: ").strip()  # 파일 경로를 받는다.
                    imported, skipped, errors = service.import_csv(Path(csv_source))  # CSV를 가져온다.
                    for err in errors:  # 오류 내역을 순회한다.
                        print(f"[건너뜀] {err}")  # 건너뛴 이유를 출력한다.
                    print(f"[완료] imported={imported}, skipped={skipped}")  # 최종 통계를 출력한다.
                elif csv_action in ["2", "export"]:  # 내보내기를 선택한 경우다.
                    csv_target = input("저장할 CSV 파일 경로: ").strip()  # 대상 경로를 받는다.
                    e_month = input("내보낼 월(YYYY-MM, 생략 시 전체): ").strip() or None  # 월 조건을 받는다.
                    count = service.export_csv(Path(csv_target), month=e_month)  # CSV로 내보낸다.
                    print(f"[완료] {csv_target} ({count} records)")  # 완료 메시지를 출력한다.
                else:  # 잘못된 번호를 누른 경우다.
                    print("❌ ⚠️ 잘못된 선택이다.")  # 안내를 출력한다.

            else:  # 메뉴에 없는 번호를 입력한 경우다.
                print("\n\n ❌ ⚠️ 1부터 9 또는 q를 입력해야 한다. ❌")  # 올바른 선택 안내를 출력한다.

        except (ValidationError, NotFoundError, ConflictError) as error:  # 서비스에서 발생한 비즈니스 검증 오류를 잡는다.
            print_error(error.message, error.hint)  # 에러 메시지와 힌트를 출력한다.
