# 이 파일은 CLI 화면에 글자, 구분선, 에러 메시지 등을 깔끔하게 출력하는 기능을 담당한다.

from typing import Optional  # 함수 인자의 값이 비어 있을 수도(None) 있음을 표시하기 위해 가져온다.


def print_divider(char: str = "=", length: int = 56) -> None:  # 지정한 문자(char)로 긴 구분 장식선을 화면에 출력한다.
    print(char * length)  # 문자를 지정한 길이만큼 반복해서 한 줄로 출력한다.


def print_error(message: str, hint: Optional[str] = None) -> None:  # 오류 원인과 해결 힌트를 표준적인 서식으로 출력한다.
    print(f"[오류] {message}")  # 빨간 느낌표 역할을 하는 오류 메시지를 출력한다.
    if hint:  # 해결을 돕는 힌트 문구가 전달되었는지 확인한다.
        print(f"[힌트] {hint}")  # 사용자가 취할 수 있는 해결 행동을 출력한다.


def print_warning(message: str) -> None:  # 사용자에게 주의를 주는 경고 문구를 출력한다.
    print(f"[경고] {message}")  # 경고 말머리를 붙여서 출력한다.


def print_success(message: str) -> None:  # 작업이 정상적으로 완료되었음을 알리는 메시지를 출력한다.
    print(f"[완료] {message}")  # 완료 말머리를 붙여서 출력한다.


def print_section_title(title: str) -> None:  # 특정 작업 영역으로 들어갈 때 작은 소제목을 출력한다.
    print(f"\n⏬ [{title}] ⏬")  # 눈에 잘 띄는 화살표 기호와 함께 소제목을 출력한다.
