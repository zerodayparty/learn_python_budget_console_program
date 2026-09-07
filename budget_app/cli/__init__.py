# 이 파일은 cli 패키지의 대문(진입점) 역할을 하며, 외부에서 사용할 핵심 함수들을 공개한다.

from budget_app.cli.app import execute, main  # app 모듈에서 실행기, 메인 진입 함수를 가져온다.
from budget_app.cli.interactive import run_interactive_console  # 대화형 콘솔 실행 함수를 가져온다.
from budget_app.cli.parser import build_parser  # parser 모듈에서 명령어 파서 생성 함수를 가져온다.

__all__ = ["build_parser", "execute", "main", "run_interactive_console"]  # 패키지 외부로 공개할 대표 이름 목록이다.
