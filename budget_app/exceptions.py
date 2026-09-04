# 이 파일은 프로그램에서 예상할 수 있는 오류 종류를 정의한다.


class BudgetAppError(Exception):  # 사용자에게 설명할 수 있는 모든 프로그램 오류의 부모 클래스다.
    def __init__(self, message: str, hint: str) -> None:  # 오류 원인과 해결 힌트를 함께 받는다.
        super().__init__(message)  # Exception 부모 클래스에 오류 원인을 전달한다.
        self.message = message  # 화면에 보여 줄 오류 원인을 저장한다.
        self.hint = hint  # 화면에 보여 줄 해결 방법을 저장한다.


class ValidationError(BudgetAppError):  # 잘못된 날짜나 금액 같은 입력 오류를 나타낸다.
    pass  # 부모 클래스의 기능을 그대로 사용하므로 추가 코드는 필요 없다.


class NotFoundError(BudgetAppError):  # 요청한 거래나 예산을 찾지 못한 오류를 나타낸다.
    pass  # 부모 클래스의 기능을 그대로 사용하므로 추가 코드는 필요 없다.


class ConflictError(BudgetAppError):  # 중복 또는 사용 중인 데이터 때문에 작업할 수 없는 오류다.
    pass  # 부모 클래스의 기능을 그대로 사용하므로 추가 코드는 필요 없다.


class DataFileError(BudgetAppError):  # 저장 파일의 내용이 손상된 경우를 나타낸다.
    pass  # 부모 클래스의 기능을 그대로 사용하므로 추가 코드는 필요 없다.
