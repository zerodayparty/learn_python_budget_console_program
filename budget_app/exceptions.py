# [가계부 프로그램 예외(오류) 처리 동작 원리]
# 1. 에러 던지기(raise): 코드 실행 중 비정상적인 입력이나 상황을 발견하면 'raise 에러클래스(메시지, 힌트)'로 에러를 던진다.
# 2. 에러 보관(init): 부모 클래스인 BudgetAppError가 생성되면서 오류 원인(message)과 해결 방법(hint)을 자기 자신(self)에 보관한다.
# 3. 파이썬 시스템 등록(super): 조상 클래스인 Exception에 메시지를 넘겨주어 파이썬 표준 에러 시스템으로 등록한다.
# 4. 상속 분류(inheritance): ValidationError, NotFoundError 등은 부모의 기능을 그대로 물려받아(pass) 에러의 종류(이름표)만 구분한다.
# 5. 에러 수습(try-except): cli.py(화면단)에서 try-except로 에러를 가로채서, 프로그램이 튕기지 않고 화면에 친절하게 힌트를 출력한다.


class BudgetAppError(Exception):  # 파이썬 기본 에러인 Exception을 상속받아 프로그램 전용 기본 에러를 만든다.
    def __init__(self, message: str, hint: str) -> None:  # 에러 객체가 만들어질 때 오류 원인과 해결 힌트를 전달받는다.
        super().__init__(message)  # Exception 조상 클래스에 오류 원인을 전달하여 파이썬 정식 에러로 등록한다.
        self.message = message  # 에러 객체 내부의 message 속성에 사용자가 읽을 오류 원인을 저장한다.
        self.hint = hint  # 에러 객체 내부의 hint 속성에 사용자가 취해야 할 행동 힌트를 저장한다.


# ==============================================================================
# 아래 클래스들은 모두 BudgetAppError를 상속받는다.
# 의사가 질병을 두통, 복통으로 나누듯, 에러의 성격에 따라 이름표를 분류해 둔 것이다.
# pass를 쓴 이유: 부모 클래스(BudgetAppError)의 기능을 100% 그대로 쓰므로 추가 코드가 필요 없다.
# ==============================================================================


class ValidationError(BudgetAppError):  # 날짜 형식이나 금액이 잘못된 경우처럼 사용자 입력 검증이 실패했을 때 발생한다.
    pass  # 부모의 __init__ 동작(message, hint 저장)을 그대로 사용한다.


class NotFoundError(BudgetAppError):  # 삭제하거나 수정하려는 거래 번호나 카테고리를 찾지 못했을 때 발생한다.
    pass  # 부모의 __init__ 동작(message, hint 저장)을 그대로 사용한다.


class ConflictError(BudgetAppError):  # 이미 존재하는 카테고리를 중복 생성하거나, 거래가 연결된 카테고리를 지우려 할 때 발생한다.
    pass  # 부모의 __init__ 동작(message, hint 저장)을 그대로 사용한다.


class DataFileError(BudgetAppError):  # 저장된 JSON 파일이 깨져 있거나 파일 읽기/쓰기에 실패했을 때 발생한다.
    pass  # 부모의 __init__ 동작(message, hint 저장)을 그대로 사용한다.
