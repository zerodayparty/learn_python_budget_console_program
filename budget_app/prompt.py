# 이 파일은 사용자와 대화하듯 키보드 입력을 받고 올바른 값인지 검사하는 기능을 담당한다.

from typing import Callable, Optional  # 함수 타입과 값이 없을 수도 있는 타입을 표시하기 위해 가져온다.

from budget_app.exceptions import NotFoundError, ValidationError  # 입력 오류와 데이터 없음 오류를 다루기 위해 가져온다.
from budget_app.models import Transaction  # 수정 결과로 돌려줄 거래 데이터 클래스를 가져온다.
from budget_app.output import print_error  # 오류와 힌트를 예쁘게 출력해 주는 도구를 가져온다.
from budget_app.services import BudgetService  # 카테고리 확인 및 거래 수정을 호출할 서비스 객체 타입이다.


def prompt_until_valid(label: str, validator: Callable[[str], object]) -> object:  # 올바른 값을 입력받을 때까지 사용자에게 계속 묻는다.
    while True:  # 검사를 무사히 통과할 때까지 무한히 입력을 다시 받는다.
        raw = input(label)  # 사용자에게 질문 라벨을 띄우고 키보드로 한 줄 입력을 받는다.
        try:  # 입력받은 글자가 규칙에 맞는지 검사를 시도한다.
            return validator(raw)  # 검사를 통과하면 즉시 변환된 값을 돌려주며 반복을 마친다.
        except ValidationError as error:  # 사용자가 잘못 입력해 유효성 검사 에러가 난 경우다.
            print_error(error.message, error.hint)  # 에러 원인과 올바른 입력 힌트를 화면에 출력한다.


def prompt_registered_category(service: BudgetService) -> str:  # 가계부에 이미 등록된 카테고리를 입력할 때까지 반복해서 묻는다.
    while True:  # 등록된 카테고리를 입력할 때까지 무한 반복한다.
        category = input("카테고리: ").strip()  # 카테고리 이름을 입력받고 앞뒤 공백을 깔끔하게 제거한다.
        if category in service.list_categories():  # 입력한 카테고리가 등록된 카테고리 목록에 있는지 확인한다.
            return category  # 등록된 카테고리면 즉시 이름을 돌려주며 반복을 마친다.
        available = ", ".join(service.list_categories())  # 현재 사용 가능한 카테고리들을 쉼표로 연결한다.
        print_error("등록되지 않은 카테고리다.", f"사용 가능: {available}")  # 오류 문구와 선택 가능한 목록 힌트를 출력한다.


def prompt_update_interactive(service: BudgetService, transaction_id: Optional[str] = None) -> Transaction:  # 거래 id를 찾고 수정할 값을 대화형으로 입력받아 수정한다.
    target_id = transaction_id  # 매개변수로 전달된 거래 id를 우선 대상 변수에 넣는다.
    if target_id is None or not target_id.strip():  # 거래 id가 전달되지 않았거나 빈칸인지 확인한다.
        target_id = input("수정할 거래 id: ").strip()  # 사용자에게 직접 수정할 거래 id를 입력받는다.

    found = service.transactions.find_by_id(target_id)  # 저장소에서 해당 id를 가진 거래가 있는지 찾아본다.
    if found is None:  # 찾으려는 거래가 저장 파일에 없는 경우다.
        raise NotFoundError(f"id '{target_id}' 거래가 없다.", "list 명령으로 존재하는 거래 id를 확인한다.")  # 에러를 일으킨다.

    tags_text = ",".join(found.tags)  # 기존 거래의 태그들을 쉼표로 이어 붙인다.
    print(f"[현재 내역] {found.date} | {found.type} | {found.category} | {found.amount} | {found.memo} | {tags_text}")  # 현재 저장된 거래 상세 정보를 보여준다.
    print("수정할 값을 입력한다. (기존 값을 유지하려면 아무것도 입력하지 않고 엔터를 누른다.)")  # 수정 방법 안내를 출력한다.

    date_input = input(f"새 날짜(YYYY-MM-DD) [현재: {found.date}]: ").strip()  # 새 날짜 입력을 받는다.
    type_input = input(f"새 타입(income/expense) [현재: {found.type}]: ").strip()  # 새 타입 입력을 받는다.
    category_input = input(f"새 카테고리 [현재: {found.category}]: ").strip()  # 새 카테고리 입력을 받는다.
    amount_input = input(f"새 금액(양의 정수) [현재: {found.amount}]: ").strip()  # 새 금액 입력을 받는다.
    memo_input = input(f"새 메모 [현재: {found.memo}]: ")  # 새 메모 입력을 받는다.
    tags_input = input(f"새 태그(쉼표 구분) [현재: {tags_text}]: ")  # 새 태그 입력을 받는다.

    updated_date = date_input if date_input else None  # 입력값이 있으면 쓰고, 빈칸이면 None(기존 유지)으로 둔다.
    updated_type = type_input if type_input else None  # 입력값이 있으면 쓰고, 빈칸이면 None(기존 유지)으로 둔다.
    updated_category = category_input if category_input else None  # 입력값이 있으면 쓰고, 빈칸이면 None(기존 유지)으로 둔다.
    updated_amount = amount_input if amount_input else None  # 입력값이 있으면 쓰고, 빈칸이면 None(기존 유지)으로 둔다.
    updated_memo = memo_input if memo_input.strip() else (None if memo_input == "" else "")  # 메모 변경 여부를 결정한다.
    updated_tags = tags_input if tags_input.strip() else (None if tags_input == "" else "")  # 태그 변경 여부를 결정한다.

    return service.update_transaction(  # 결정된 값들을 서비스에 전달하여 실제로 파일 내용을 수정하고 결과를 돌려준다.
        transaction_id=target_id,  # 대상 거래 id다.
        date=updated_date,  # 수정할 날짜다.
        transaction_type=updated_type,  # 수정할 타입이다.
        category=updated_category,  # 수정할 카테고리다.
        amount=updated_amount,  # 수정할 금액이다.
        memo=updated_memo,  # 수정할 메모다.
        tags=updated_tags,  # 수정할 태그다.
    )  # 거래 수정 호출을 마친다.
