# 이 파일은 가계부 데이터(거래 내역, 요약 통계, 메뉴 화면)를 터미널 화면(View)으로 만든다.

from budget_app.cli.output import print_divider, print_warning  # CLI 전용 구분선과 경고 문구 출력 도구를 가져온다.
from budget_app.models import MonthlySummary, Transaction  # 화면에 띄울 거래 데이터와 통계 요약 데이터 클래스를 가져온다.


def print_transaction(transaction: Transaction) -> None:  # 거래 한 건을 세로선(|)으로 구분된 깔끔한 한 줄로 출력한다.
    tags = ",".join(transaction.tags)  # 여러 개의 태그를 쉼표로 연결해 하나의 문자열로 만든다.
    columns = [  # 화면에 나란히 보여줄 데이터들을 순서대로 목록에 담는다.
        transaction.id,  # 1열: 거래 고유 식별 번호다.
        transaction.date,  # 2열: 거래가 일어난 날짜다.
        transaction.type,  # 3열: 수입(income) 또는 지출(expense) 유형이다.
        transaction.category,  # 4열: 카테고리 이름이다.
        str(transaction.amount),  # 5열: 금액을 글자로 변환한 값이다.
        transaction.memo,  # 6열: 메모 내용이다.
        tags,  # 7열: 쉼표로 이은 태그 목록이다.
    ]  # 7개 열 데이터 구성을 마친다.
    line = " | ".join(columns)  # 열 사이에 ' | ' 구분 기호를 넣어 하나의 문자열로 합친다.
    print(line)  # 완성된 거래 한 줄을 콘솔 화면에 출력한다.


def print_summary(summary: MonthlySummary) -> None:  # 한 달 동안의 수입, 지출, 예산 요약 결과를 출력한다.
    if summary.transaction_count == 0:  # 해당 월에 거래가 하나도 없는지 확인한다.
        print(f"{summary.month}: 데이터 없음")  # 거래 기록이 없음을 명확하게 출력한다.
    else:  # 거래가 1건 이상 존재하는 정상적인 경우다.
        print(f"총 수입: {summary.total_income}원")  # 총수입 합계를 원 단위로 출력한다.
        print(f"총 지출: {summary.total_expense}원")  # 총지출 합계를 원 단위로 출력한다.
        print(f"잔액: {summary.balance}원")  # 총수입에서 총지출을 뺀 순수 잔액을 출력한다.

    if summary.budget is not None:  # 해당 월에 목표 예산이 설정되어 있는지 확인한다.
        print(f"예산: {summary.budget}원 (사용률 {summary.budget_usage:.1f}%)")  # 예산 금액과 사용률 백분율을 출력한다.
        if summary.is_over_budget:  # 지출이 예산을 넘어섰는지 확인한다.
            print_warning("월 예산을 초과했다.")  # 예산 초과 경고 문구를 출력한다.

    if summary.transaction_count > 0 and summary.category_expenses:  # 거래가 있고 카테고리별 지출 순위가 존재하는지 확인한다.
        print("지출 카테고리 TOP")  # 상위 지출 카테고리 목록의 시작을 알리는 제목을 출력한다.
        for rank, (category, amount) in enumerate(summary.category_expenses, start=1):  # 1위부터 순서대로 번호를 붙여 읽는다.
            print(f"{rank}) {category} {amount}원")  # 순위, 카테고리 이름, 지출 금액을 한 줄로 출력한다.


def print_interactive_header() -> None:  # 대화형 모드 시작 시 맨 위에 보여줄 환영 배너를 출력한다.
    print("\n" + "=" * 56)  # 상단 구분 장식선을 출력한다.
    print("  💰 파일 기반 가계부 콘솔 프로그램 (대화형 콘솔 모드)")  # 프로그램 제목을 중앙에 출력한다.
    print("=" * 56)  # 하단 구분 장식선을 출력한다.


def print_main_menu() -> None:  # 사용자가 번호를 고를 수 있도록 1~9번 및 종료 메뉴 목록을 화면에 출력한다.
    print("\n\n⬛️⬛️⬛️⬛️⬛️[가계부 메인 메뉴]⬛️⬛️⬛️⬛️⬛️")  # 메뉴판 제목을 강조 이모지와 함께 출력한다.
    print("  1. 거래 추가 (add)")  # 1번 메뉴: 거래 추가를 안내한다.
    print("  2. 최근 거래 목록 (list)")  # 2번 메뉴: 거래 목록 조회를 안내한다.
    print("  3. 조건별 거래 검색 (search)")  # 3번 메뉴: 조건 검색을 안내한다.
    print("  4. 거래 수정 (update - 대화형)")  # 4번 메뉴: 대화형 거래 수정을 안내한다.
    print("  5. 거래 삭제 (delete)")  # 5번 메뉴: 거래 삭제를 안내한다.
    print("  6. 월별 요약 및 예산 현황 (summary)")  # 6번 메뉴: 월별 요약을 안내한다.
    print("  7. 월 예산 설정 및 조회 (budget)")  # 7번 메뉴: 예산 관리를 안내한다.
    print("  8. 카테고리 관리 (category)")  # 8번 메뉴: 카테고리 관리를 안내한다.
    print("  9. CSV 내보내기 / 가져오기 (export / import)")  # 9번 메뉴: CSV 작업을 안내한다.
    print("  q. 프로그램 종료 (quit)")  # q 메뉴: 프로그램 종료를 안내한다.
