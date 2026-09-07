# 이 파일은 python -m budget_app 명령이 실행할 시작 지점이다.

import sys  # sys는 프로그램 종료 코드를 운영체제에 전달하는 도구다.

from budget_app.cli.app import main  # cli 패키지 내부의 app 모듈에서 시작 함수를 직접 가져온다.


if __name__ == "__main__":  # 이 파일이 python -m 명령으로 직접 실행되었는지 확인한다.
    sys.exit(main())  # main의 0 또는 0이 아닌 값을 실제 프로세스 종료 코드로 전달한다.
