# 이 파일은 터미널 명령줄 옵션과 도움말(--help) 구조를 정의하는 전담 파서 모듈이다.

import argparse  # argparse는 명령어와 --옵션을 해석하고 --help를 자동 생성하는 표준 라이브러리다.

from budget_app.constants import (  # 공통 상수 모듈에서 파서 기본값을 가져온다.
    DEFAULT_DATA_DIR,  # 기본 데이터 저장 폴더 이름이다.
    DEFAULT_LIST_LIMIT,  # 목록 출력 시 기본 개수다.
    DEFAULT_SUMMARY_TOP,  # 요약 시 상위 카테고리 기본 개수다.
    TRANSACTION_TYPES,  # 거래 허용 타입 튜플이다.
)  # 상수 가져오기를 끝낸다.



# ✅ 문자열을 정수로 바꾸는 함수
def _positive_integer(value: str) -> int:  # argparse 옵션 값을 1 이상의 정수로 검사한다.
    try:  # 문자열을 정수로 바꾸는 작업을 시도한다.
        number = int(value)  # 터미널에서 받은 문자열을 정수로 변환한다.
    except ValueError as error:  # 정수로 바꿀 수 없는 글자면 이 오류가 발생한다.
        raise argparse.ArgumentTypeError("1 이상의 정수를 입력한다.") from error  # argparse가 사용법과 함께 오류를 출력하게 한다.
    if number <= 0:  # 변환한 숫자가 0 또는 음수인지 검사한다.
        raise argparse.ArgumentTypeError("1 이상의 정수를 입력한다.")  # argparse가 올바른 범위를 출력하게 한다.
    return number  # 검사를 통과한 양의 정수를 돌려준다.




# ✅ ✏️ [study] 'argparse' python 표준 라이브러리
# (ArgumentParser, subparser, add_parser, add_argument, argparse.ArgumentTypeError 등등 'argparse' 표준 라이브러리를 많이 사용하고 있다.)
# argument는 그냥 프로그램에 전달하는 값이라고 생각하면 된다. 
# parse는 복잡한 입력을 분석해서 프로그램이 사용할 수 있는 형태로 변환한다.
# 즉, 전달하는 값을 받아서 분석하여 프로그램이 사용할 수 있는 형태로 변환해주는 것이다.
# 단 몇 줄의 설정만으로 버그 없이 안전한 터미널 프로그램을 만들 수 있다.
# 'python main.py --number 50'  이런 방식으로 옵션과 값 형태를 줄 수 있다.

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
        help="카테고리 추가·목록·확인·삭제",  # 전체 도움말에 보일 짧은 설명을 정한다.
        description="거래에서 사용할 카테고리를 관리한다.",  # category 도움말에 보일 상세 설명을 정한다.
    )  # category 명령 해석기 만들기를 끝낸다.
    category_actions = category_parser.add_subparsers(dest="category_action", required=True, title="카테고리 작업")  # add, list, exists, remove 중 하나를 선택하게 한다.
    category_add_parser = category_actions.add_parser("add", help="카테고리 추가")  # category add 명령 해석기를 만든다.
    category_add_parser.add_argument("--name", help="이름이며 생략하면 대화형으로 입력")  # 옵션 또는 대화형으로 이름을 받는다.
    category_actions.add_parser("list", help="카테고리 목록")  # category list와 --help를 등록한다.
    category_exists_parser = category_actions.add_parser("exists", help="특정 카테고리 존재 확인")  # category exists 명령 해석기를 만든다.
    category_exists_parser.add_argument("--name", help="이름이며 생략하면 대화형으로 입력")  # 옵션 또는 대화형으로 확인할 이름을 받는다.
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
