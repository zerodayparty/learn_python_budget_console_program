# 이 파일은 budgets.jsonl 월별 예산 파일만 읽고 쓰는 저장소를 담당한다.

from pathlib import Path  # Path는 예산 파일 경로를 객체로 다루게 해 준다.
from typing import Any, Dict, List, Optional  # JSON 사전과 예산 목록 및 생략 가능한 반환 타입을 표시한다.

from budget_app.constants import BUDGETS_FILENAME, ErrorMessages  # 예산 파일 이름과 오류 메시지를 가져온다.
from budget_app.exceptions import DataFileError  # 손상된 예산 파일 오류를 알리기 위해 가져온다.
from budget_app.repositories.jsonl_storage import atomic_write_jsonl, parse_json_line  # 공통 JSONL 파일 도구들을 가져온다.
from budget_app.validators import validate_amount, validate_month  # 예산 월과 금액 검증 함수를 가져온다.


class BudgetStore:  # 월별 예산의 파일 저장과 조회를 담당한다.
    def __init__(self, data_dir: Path) -> None:  # 저장 폴더를 받아 예산 파일을 준비한다.
        data_dir.mkdir(parents=True, exist_ok=True)  # 부모 폴더까지 만들고 이미 있으면 그대로 둔다.
        self.path = data_dir / BUDGETS_FILENAME  # 상수로 관리되는 예산 파일 경로를 만든다.
        self.path.touch(exist_ok=True)  # 첫 실행이고 파일이 없으면 빈 파일을 만든다.

    def _load_all(self) -> Dict[str, int]:  # 저장된 월별 예산을 사전으로 읽는다.
        budgets: Dict[str, int] = {}  # 월을 열쇠로, 금액을 값으로 담을 빈 사전을 만든다.
        with self.path.open("r", encoding="utf-8") as data_file:  # 예산 파일을 UTF-8 읽기 모드로 연다.
            for line in data_file:  # 파일을 한 줄씩 읽는다.
                if not line.strip():  # 현재 줄이 빈 줄인지 확인한다.
                    continue  # 빈 줄은 무시하고 다음 줄로 넘어간다.
                raw = parse_json_line(line, self.path)  # JSONL 한 줄을 Python 사전으로 바꾼다.
                if "month" not in raw or "amount" not in raw:  # 필수 month와 amount 항목이 모두 있는지 확인한다.
                    raise DataFileError(*ErrorMessages.BUDGET_MISSING_FIELDS)  # 예산 필수 필드 누락 오류를 알린다.
                month = validate_month(str(raw["month"]))  # 저장된 월을 YYYY-MM 형식으로 검사한다.
                amount = validate_amount(raw["amount"])  # 저장된 예산을 양의 정수로 검사한다.
                if month in budgets:  # 같은 월을 이미 읽었는지 확인한다.
                    raise DataFileError(*ErrorMessages.BUDGET_DUPLICATE_MONTH)  # 중복 예산 월 오류를 알린다.
                budgets[month] = amount  # 검사한 월과 금액을 사전에 저장한다.
        return budgets  # 모든 월별 예산을 돌려준다.

    def get(self, month: str) -> Optional[int]:  # 특정 월에 설정된 예산을 찾는다.
        cleaned_month = validate_month(month)  # 찾을 월의 형식을 검사한다.
        return self._load_all().get(cleaned_month)  # 저장된 예산을 돌려주고 없으면 None을 돌려준다.

    def set(self, month: str, amount: object) -> int:  # 특정 월의 예산을 새로 저장하거나 수정한다.
        cleaned_month = validate_month(month)  # 저장할 월의 형식을 검사한다.
        cleaned_amount = validate_amount(amount)  # 저장할 금액을 양의 정수로 검사한다.
        budgets = self._load_all()  # 현재 저장된 모든 예산을 읽는다.
        budgets[cleaned_month] = cleaned_amount  # 같은 월은 수정하고 새 월은 추가한다.
        records: List[Dict[str, Any]] = []  # 예산 JSON 객체를 담을 빈 목록을 만든다.
        for saved_month in sorted(budgets):  # 저장된 월을 오래된 월부터 하나씩 꺼낸다.
            records.append({"month": saved_month, "amount": budgets[saved_month]})  # 현재 월과 금액을 JSON 저장 목록에 추가한다.
        atomic_write_jsonl(self.path, records)  # 전체 예산을 임시 파일에 쓴 뒤 원본과 교체한다.
        return cleaned_amount  # 실제로 저장한 금액을 돌려준다.
