# 이 파일은 python -m budget_app 명령이 실행할 시작 지점이다.

import sys  # sys는 프로그램 종료 코드를 운영체제에 전달하는 도구다.

from budget_app.cli import main  # 실제 명령 해석과 실행을 담당하는 main 함수를 가져온다.


if __name__ == "__main__":  # 이 파일이 python -m 명령으로 직접 실행되었는지 확인한다.
    sys.exit(main())  # main의 0 또는 0이 아닌 값을 실제 프로세스 종료 코드로 전달한다.
