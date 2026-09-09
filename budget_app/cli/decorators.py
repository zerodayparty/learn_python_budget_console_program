# 이 파일은 여러 CLI 명령에 공통인 오류 출력 기능을 데코레이터로 제공한다.

import csv  # CSV 표준 라이브러리가 발생시키는 파일 형식 오류를 잡기 위해 가져온다.
from functools import wraps  # wraps는 감싼 함수의 이름과 설명을 원래대로 보존한다.
from typing import Callable  # Callable은 함수 자체의 타입을 표시한다.

from budget_app.exceptions import BudgetAppError  # 프로그램이 예상한 사용자용 오류의 부모 클래스다.


def handle_cli_errors(function: Callable[..., int]) -> Callable[..., int]:  # 명령 함수에 공통 오류 처리 기능을 붙이는 데코레이터다.
    @wraps(function)  # 내부 함수가 원래 함수의 이름과 정보를 유지하도록 한다.
    def wrapper(*args: object, **kwargs: object) -> int:  # 어떤 인자를 받는 명령 함수든 감쌀 수 있는 내부 함수다.
        try:  # 원래 명령 실행을 시도한다.
            return function(*args, **kwargs)  # 원래 함수를 실행하고 정상 종료 코드 0 등을 그대로 돌려준다.
        except BudgetAppError as error:  # 검증, 없음, 충돌, 파일 손상처럼 예상한 오류를 잡는다.
            print(f"[오류] {error.message}")  # 스택트레이스 대신 사용자가 이해할 원인을 출력한다.
            print(f"[힌트] {error.hint}")  # 사용자가 다음에 할 해결 방법을 출력한다.
            return 2  # 0이 아닌 종료 코드로 실패를 운영체제에 알린다.
        except (OSError, UnicodeError, csv.Error) as error:  # 파일 접근, 글자 인코딩, CSV 문법 오류를 잡는다.
            print(f"[오류] 파일을 처리하지 못했다: {error}")  # 실제 파일 오류 원인을 짧게 출력한다.
            print("[힌트] 경로, 읽기·쓰기 권한, UTF-8 파일 형식을 확인한다.")  # 공통 해결 방법을 출력한다.
            return 3  # 파일 처리 실패를 구분하는 0이 아닌 종료 코드를 돌려준다.
        except (EOFError, KeyboardInterrupt):  # 입력 종료나 Control+C 취소를 잡는다.
            print("[오류] 사용자가 강제로 종료하여 프로그램이 중단되었습니다.")  # 프로그램이 중단된 원인을 출력한다.
            print("[힌트] 명령을 다시 실행하고 입력을 끝까지 완료한다.")  # 다시 실행하는 해결 방법을 출력한다.
            return 130  # 터미널에서 사용자 중단을 나타내는 종료 코드를 돌려준다.
        except Exception as error:  # 미리 분류하지 못한 오류도 스택트레이스 없이 잡는다.
            print(f"[오류] 예상하지 못한 문제가 발생했다: {error}")  # 확인 가능한 실제 오류 문구를 출력한다.
            print("[힌트] 입력과 data 파일을 확인한 뒤 같은 명령을 다시 실행한다.")  # 사용자가 먼저 확인할 해결 방법을 출력한다.
            return 1  # 일반 실행 실패를 뜻하는 0이 아닌 종료 코드를 돌려준다.

    return wrapper  # 공통 오류 처리 기능이 붙은 새 함수를 돌려준다.



# 🟢 해설

# 공통 오류 처리는 `decorators.py`의 `handle_cli_errors()` 데코레이터가 담당하고, `cli.py`의 `execute()` 위에 `@handle_cli_errors`로 실제 적용했다.  

# 오류 전달 흐름:  
# `Validator 또는 Repository에서 오류 발생 → BudgetService를 지나 execute() 밖으로 전달 → decorator wrapper()가 catch → 원인과 힌트 출력 → 0이 아닌 값 반환`  

# | 잡는 오류 | 사용자 출력 | 반환 코드 |  
# | --- | --- | --- |
# | `BudgetAppError` 계열 | `[오류] message`, `[힌트] hint` | 2 |  
# | `OSError`, `UnicodeError`, `csv.Error` | 파일 처리 원인과 경로·권한·UTF-8 확인 힌트 | 3 |  
# | `EOFError`, `KeyboardInterrupt` | 입력 중단 원인과 재실행 힌트 | 130 |  
# | 그 밖의 `Exception` | 예상하지 못한 문제와 데이터 확인 힌트 | 1 |  

# | 종료 코드 | 코드가 의미하는 상황 |  
# | --- | --- |
# | 0 | 정상 실행 |  
# | 1 | 분류하지 못한 실행 오류 |  
# | 2 | 검증 실패, 없는 데이터, 충돌, 손상 데이터 또는 argparse 사용법 오류 |  
# | 3 | 파일 접근, 문자 인코딩, CSV 형식 오류 |  
# | 130 | 사용자가 Control+C 또는 입력 종료로 중단 |  