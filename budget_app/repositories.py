# 이 파일은 JSONL 파일 생성, 읽기, 추가, 안전한 전체 교체를 담당한다.

import json  # json은 Python 데이터를 JSON(JavaScript Object Notation) 문자열로 바꾸는 도구다.
import os  # os는 파일 위치 이동과 디스크 동기화 같은 운영체제 기능을 제공한다.
import tempfile  # tempfile은 안전한 임시 파일을 만드는 표준 라이브러리다.
from pathlib import Path  # Path는 파일과 폴더 경로를 객체로 다루게 해 준다.
from typing import Any, Dict, Iterable, Iterator, List, Optional  # 함수가 주고받는 값의 자료형을 표시한다.

from budget_app.exceptions import ConflictError, DataFileError  # 중복과 파일 손상을 사용자에게 설명할 오류다.
from budget_app.models import Transaction  # 저장하고 읽을 거래 데이터 클래스를 가져온다.
from budget_app.validators import validate_amount, validate_category_name, validate_month  # 카테고리와 예산 파일을 검사할 함수다.

DEFAULT_CATEGORIES = ("food", "transport", "rent", "salary", "utilities", "health", "leisure", "other")  # 첫 실행 때 만들 기본 카테고리다.


def _json_line(record: Dict[str, Any]) -> str:  # 사전 한 개를 JSONL 한 줄로 바꾼다.
    return json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"  # 한글을 유지하고 마지막에 줄바꿈을 붙인다.


def _atomic_write_jsonl(path: Path, records: Iterable[Dict[str, Any]]) -> None:  # 여러 데이터를 임시 파일에 쓴 뒤 원본과 한 번에 교체한다.
    temporary_path: Optional[Path] = None  # 작업 실패 때 지울 임시 파일 경로를 미리 준비한다.
    try:  # 임시 파일 생성부터 원본 교체까지 안전하게 시도한다.
        with tempfile.NamedTemporaryFile(  # 같은 폴더에 이름이 겹치지 않는 임시 파일을 만든다.
            mode="w",  # 텍스트를 새로 쓰는 모드로 연다.
            encoding="utf-8",  # 모든 글자를 UTF-8(Unicode Transformation Format 8-bit)로 저장한다.
            dir=str(path.parent),  # 원자적 교체를 위해 원본과 같은 폴더에 만든다.
            prefix=f".{path.name}.",  # 임시 파일임을 알아볼 수 있는 이름 앞부분이다.
            suffix=".tmp",  # temporary의 줄임말인 tmp 확장자를 붙인다.
            delete=False,  # 파일을 닫은 뒤 os.replace가 사용할 수 있도록 자동 삭제를 끈다.
        ) as temporary_file:  # 생성한 임시 파일을 temporary_file 이름으로 사용한다.
            temporary_path = Path(temporary_file.name)  # 나중에 교체하거나 삭제할 수 있도록 경로를 저장한다.
            for record in records:  # 저장할 데이터를 한 건씩 꺼낸다.
                temporary_file.write(_json_line(record))  # 각 데이터를 JSONL 한 줄로 임시 파일에 쓴다.
            temporary_file.flush()  # Python 메모리에 남은 내용을 운영체제로 보낸다.
            os.fsync(temporary_file.fileno())  # 운영체제 버퍼의 내용도 실제 디스크에 기록하도록 요청한다.
        os.replace(temporary_path, path)  # 임시 파일을 원본 경로로 원자적으로 교체한다.
        temporary_path = None  # 교체가 끝났으므로 삭제할 임시 파일이 없다고 표시한다.
    finally:  # 성공과 실패에 상관없이 남은 임시 파일을 정리한다.
        if temporary_path is not None and temporary_path.exists():  # 교체되지 않은 임시 파일이 실제로 남았는지 확인한다.
            temporary_path.unlink()  # 실패 중에 남은 임시 파일만 삭제한다.


def _parse_json_line(line: str, path: Path) -> Dict[str, Any]:  # JSONL 한 줄을 Python 사전으로 바꾼다.
    try:  # JSON 해석을 시도한다.
        parsed = json.loads(line)  # JSON 문자열을 Python 값으로 변환한다.
    except json.JSONDecodeError as error:  # 문법이 깨진 JSON이면 이 오류가 발생한다.
        message = f"{path.name} 파일에 손상된 JSONL 줄이 있다."  # 사용자에게 보여 줄 파일 오류 원인을 저장한다.
        hint = "파일을 UTF-8 JSONL 형식으로 수정하거나 백업으로 복구한다."  # 사용자에게 보여 줄 해결 방법을 저장한다.
        raise DataFileError(message, hint) from error  # 저장한 원인과 힌트로 파일 오류를 발생시킨다.
    if not isinstance(parsed, dict):  # 한 줄의 결과가 사전 객체인지 검사한다.
        message = f"{path.name} 파일의 한 줄이 JSON 객체가 아니다."  # 사용자에게 보여 줄 파일 오류 원인을 저장한다.
        hint = "각 줄을 중괄호로 된 JSON 객체 한 개로 저장한다."  # 필요한 JSONL 저장 모양을 해결 방법으로 저장한다.
        raise DataFileError(message, hint)  # 저장한 원인과 힌트로 파일 오류를 발생시킨다.
    return parsed  # 검사한 사전을 돌려준다.


def _iter_lines_reverse(path: Path, block_size: int = 8192) -> Iterator[str]:  # 큰 파일을 통째로 읽지 않고 마지막 줄부터 읽는다.
    with path.open("rb") as data_file:  # byte 단위 위치 이동을 위해 파일을 Read Binary(이진 읽기) 모드로 연다.
        data_file.seek(0, os.SEEK_END)  # 읽기 위치를 파일의 맨 끝으로 옮긴다.
        position = data_file.tell()  # 현재 끝 위치가 몇 번째 byte인지 저장한다.
        remaining = b""  # 블록 경계에서 잘린 한 줄의 일부를 잠시 보관한다.
        while position > 0:  # 파일의 맨 앞에 도달할 때까지 반복한다.
            read_size = min(block_size, position)  # 이번에 읽을 크기를 파일 남은 크기보다 넘지 않게 정한다.
            position -= read_size  # 읽기 시작 위치를 앞쪽으로 이동한다.
            data_file.seek(position)  # 계산한 읽기 시작 위치로 이동한다.
            block = data_file.read(read_size) + remaining  # 앞 블록과 이전에 잘린 줄을 이어 붙인다.
            lines = block.split(b"\n")  # 줄바꿈 byte를 기준으로 여러 줄을 나눈다.
            remaining = lines[0]  # 첫 조각은 앞 블록과 이어질 수 있으므로 다음 반복까지 보관한다.
            for raw_line in reversed(lines[1:]):  # 완성된 줄들을 파일의 마지막 줄부터 거꾸로 꺼낸다.
                if raw_line.strip():  # 빈 줄이 아닌 경우만 처리한다.
                    yield raw_line.decode("utf-8")  # 한 줄만 UTF-8 문자열로 바꾸어 호출한 쪽에 전달한다.
        if remaining.strip():  # 반복이 끝난 뒤 파일 맨 앞의 줄이 남았는지 확인한다.
            yield remaining.decode("utf-8")  # 맨 앞의 마지막 남은 줄도 호출한 쪽에 전달한다.


class TransactionRepository:  # transactions.jsonl 파일만 책임지는 저장소 클래스다.
    def __init__(self, data_dir: Path) -> None:  # 저장 폴더를 받아 거래 파일을 준비한다.
        data_dir.mkdir(parents=True, exist_ok=True)  # 부모 폴더까지 만들고 이미 있으면 그대로 둔다.
        self.path = data_dir / "transactions.jsonl"  # 거래 저장 파일의 전체 경로를 만든다.
        self.path.touch(exist_ok=True)  # 첫 실행이고 파일이 없으면 빈 파일을 자동 생성한다.

    def append(self, transaction: Transaction) -> None:  # 거래 한 건을 파일 마지막에 추가한다.
        with self.path.open("a", encoding="utf-8") as data_file:  # 기존 내용을 지우지 않는 Append(추가) 모드로 연다.
            data_file.write(_json_line(transaction.to_dict()))  # 거래를 JSONL 한 줄로 바꿔 저장한다.
            data_file.flush()  # Python 메모리에 남은 내용을 운영체제로 보낸다.
            os.fsync(data_file.fileno())  # 갑작스러운 종료에 대비해 실제 디스크 기록을 요청한다.

    def iter_oldest(self) -> Iterator[Transaction]:  # 오래된 저장 순서부터 거래를 한 건씩 전달한다.
        with self.path.open("r", encoding="utf-8") as data_file:  # UTF-8 텍스트 읽기 모드로 파일을 연다.
            for line in data_file:  # 파일을 한 줄씩 읽어서 전체 파일을 메모리에 올리지 않는다.
                if line.strip():  # 빈 줄이 아닌 경우만 거래로 해석한다.
                    yield Transaction.from_dict(_parse_json_line(line, self.path))  # 한 줄을 거래 객체로 바꿔 전달한다.

    def iter_latest(self) -> Iterator[Transaction]:  # 최신 저장 순서부터 거래를 한 건씩 전달한다.
        for line in _iter_lines_reverse(self.path):  # 파일 끝에서 시작해 JSONL 한 줄씩 받는다.
            yield Transaction.from_dict(_parse_json_line(line, self.path))  # 한 줄을 거래 객체로 바꿔 전달한다.

    def find_by_id(self, transaction_id: str) -> Optional[Transaction]:  # id가 같은 거래 한 건을 찾는다.
        for transaction in self.iter_latest():  # 최신 거래부터 한 건씩 검사한다.
            if transaction.id == transaction_id:  # 현재 거래의 id가 찾는 id와 같은지 확인한다.
                return transaction  # 찾은 거래를 즉시 돌려준다.
        return None  # 끝까지 없으면 찾지 못했다는 뜻으로 None을 돌려준다.

    def replace(self, replacement: Transaction) -> bool:  # id가 같은 기존 거래를 새 거래로 교체한다.
        if self.find_by_id(replacement.id) is None:  # 교체 대상이 실제로 존재하는지 먼저 확인한다.
            return False  # 대상이 없으면 파일을 건드리지 않고 실패를 알린다.

        def replacement_records() -> Iterator[Dict[str, Any]]:  # 교체된 전체 데이터를 한 건씩 만드는 내부 제너레이터다.
            for transaction in self.iter_oldest():  # 원래 저장 순서대로 거래를 한 건씩 읽는다.
                if transaction.id == replacement.id:  # 현재 거래가 교체 대상인지 확인한다.
                    yield replacement.to_dict()  # 대상 위치에는 새 거래를 전달한다.
                else:  # 현재 거래가 교체 대상이 아닌 경우다.
                    yield transaction.to_dict()  # 기존 거래를 그대로 전달한다.

        _atomic_write_jsonl(self.path, replacement_records())  # 새 전체 내용을 임시 파일에 쓴 뒤 원본과 교체한다.
        return True  # 안전한 파일 교체가 끝났음을 알린다.

    def delete(self, transaction_id: str) -> bool:  # id가 같은 거래 한 건을 삭제한다.
        if self.find_by_id(transaction_id) is None:  # 삭제 대상이 실제로 존재하는지 먼저 확인한다.
            return False  # 대상이 없으면 파일을 건드리지 않고 실패를 알린다.

        def remaining_records() -> Iterator[Dict[str, Any]]:  # 삭제 대상을 제외한 데이터를 한 건씩 만드는 내부 제너레이터다.
            for transaction in self.iter_oldest():  # 원래 저장 순서대로 거래를 한 건씩 읽는다.
                if transaction.id != transaction_id:  # 현재 거래가 삭제 대상이 아닌지 확인한다.
                    yield transaction.to_dict()  # 삭제 대상이 아닌 거래만 새 파일로 전달한다.

        _atomic_write_jsonl(self.path, remaining_records())  # 남은 전체 내용을 임시 파일에 쓴 뒤 원본과 교체한다.
        return True  # 안전한 파일 교체가 끝났음을 알린다.


class CategoryStore:  # categories.jsonl 파일만 책임지는 저장소 클래스다.
    def __init__(self, data_dir: Path) -> None:  # 저장 폴더를 받아 카테고리 파일을 준비한다.
        data_dir.mkdir(parents=True, exist_ok=True)  # 부모 폴더까지 만들고 이미 있으면 그대로 둔다.
        self.path = data_dir / "categories.jsonl"  # 카테고리 저장 파일의 전체 경로를 만든다.
        self.path.touch(exist_ok=True)  # 첫 실행이고 파일이 없으면 빈 파일을 자동 생성한다.
        if self.path.stat().st_size == 0:  # 카테고리 파일이 비어 있는 첫 실행인지 확인한다.
            default_records: List[Dict[str, Any]] = []  # 기본 카테고리 JSON 객체를 담을 빈 목록을 만든다.
            for name in DEFAULT_CATEGORIES:  # 기본 카테고리 이름을 앞에서부터 하나씩 꺼낸다.
                record = {"name": name}  # 현재 이름으로 JSON 저장용 사전을 만든다.
                default_records.append(record)  # 만든 사전을 저장 목록에 추가한다.
            _atomic_write_jsonl(self.path, default_records)  # 완성한 기본 카테고리 목록을 안전하게 저장한다.

    def list_all(self) -> List[str]:  # 저장된 모든 카테고리를 정렬해서 돌려준다.
        categories: List[str] = []  # 읽은 카테고리를 담을 빈 목록을 만든다.
        with self.path.open("r", encoding="utf-8") as data_file:  # 카테고리 파일을 UTF-8 읽기 모드로 연다.
            for line in data_file:  # 파일을 한 줄씩 읽는다.
                if not line.strip():  # 빈 줄인지 검사한다.
                    continue  # 빈 줄은 무시하고 다음 줄로 넘어간다.
                raw = _parse_json_line(line, self.path)  # JSONL 한 줄을 Python 사전으로 바꾼다.
                if "name" not in raw:  # 필수 name 항목이 있는지 검사한다.
                    message = "categories.jsonl 파일에 name 항목이 없다."  # 사용자에게 보여 줄 파일 오류 원인을 저장한다.
                    hint = "각 줄을 {\"name\":\"food\"} 모양으로 수정한다."  # 올바른 카테고리 저장 모양을 저장한다.
                    raise DataFileError(message, hint)  # 저장한 원인과 힌트로 파일 오류를 발생시킨다.
                name = validate_category_name(str(raw["name"]))  # 카테고리 이름을 검사한다.
                if name in categories:  # 같은 이름이 이미 읽혔는지 검사한다.
                    message = "categories.jsonl 파일에 중복 카테고리가 있다."  # 사용자에게 보여 줄 중복 오류 원인을 저장한다.
                    hint = "중복된 카테고리 줄을 하나만 남긴다."  # 중복을 해결하는 방법을 저장한다.
                    raise DataFileError(message, hint)  # 저장한 원인과 힌트로 파일 오류를 발생시킨다.
                categories.append(name)  # 검사한 이름을 결과 목록에 추가한다.
        return sorted(categories)  # 이름을 가나다와 알파벳 순서로 정렬해서 돌려준다.

    def exists(self, name: str) -> bool:  # 특정 카테고리가 등록되어 있는지 확인한다.
        return name in self.list_all()  # 전체 목록 안에 같은 이름이 있는지 결과를 돌려준다.

    def add(self, name: str) -> None:  # 새 카테고리 한 개를 저장한다.
        cleaned = validate_category_name(name)  # 저장하기 전에 이름을 검사하고 정리한다.
        if self.exists(cleaned):  # 같은 이름이 이미 등록되어 있는지 검사한다.
            message = "이미 등록된 카테고리다."  # 사용자에게 보여 줄 중복 오류 원인을 저장한다.
            hint = "category list로 기존 이름을 확인한 뒤 다른 이름을 사용한다."  # 중복을 해결하는 방법을 저장한다.
            raise ConflictError(message, hint)  # 저장한 원인과 힌트로 충돌 오류를 발생시킨다.
        with self.path.open("a", encoding="utf-8") as data_file:  # 기존 내용을 유지하는 추가 모드로 파일을 연다.
            data_file.write(_json_line({"name": cleaned}))  # 카테고리 객체를 JSONL 한 줄로 저장한다.
            data_file.flush()  # Python 메모리에 남은 내용을 운영체제로 보낸다.
            os.fsync(data_file.fileno())  # 실제 디스크 기록을 요청한다.

    def remove(self, name: str) -> bool:  # 카테고리 한 개를 파일에서 삭제한다.
        cleaned = validate_category_name(name)  # 삭제할 이름을 검사하고 정리한다.
        categories = self.list_all()  # 현재 카테고리를 모두 읽는다.
        if cleaned not in categories:  # 삭제할 이름이 등록되어 있는지 검사한다.
            return False  # 등록되지 않은 이름이면 파일을 건드리지 않는다.
        remaining_records: List[Dict[str, Any]] = []  # 삭제 후 남길 카테고리 사전을 담을 빈 목록을 만든다.
        for current in categories:  # 현재 카테고리 이름을 하나씩 꺼낸다.
            if current == cleaned:  # 현재 이름이 삭제 대상인지 확인한다.
                continue  # 삭제 대상은 새 목록에 넣지 않고 다음 이름으로 넘어간다.
            record = {"name": current}  # 남길 이름으로 JSON 저장용 사전을 만든다.
            remaining_records.append(record)  # 만든 사전을 새 목록에 추가한다.
        _atomic_write_jsonl(self.path, remaining_records)  # 삭제 대상이 빠진 목록으로 파일을 안전하게 교체한다.
        return True  # 삭제가 끝났음을 알린다.


class BudgetStore:  # budgets.jsonl 파일만 책임지는 저장소 클래스다.
    def __init__(self, data_dir: Path) -> None:  # 저장 폴더를 받아 예산 파일을 준비한다.
        data_dir.mkdir(parents=True, exist_ok=True)  # 부모 폴더까지 만들고 이미 있으면 그대로 둔다.
        self.path = data_dir / "budgets.jsonl"  # 예산 저장 파일의 전체 경로를 만든다.
        self.path.touch(exist_ok=True)  # 첫 실행이고 파일이 없으면 빈 파일을 자동 생성한다.

    def _load_all(self) -> Dict[str, int]:  # 저장된 월별 예산을 사전으로 읽는다.
        budgets: Dict[str, int] = {}  # 월을 열쇠로, 금액을 값으로 담을 빈 사전을 만든다.
        with self.path.open("r", encoding="utf-8") as data_file:  # 예산 파일을 UTF-8 읽기 모드로 연다.
            for line in data_file:  # 파일을 한 줄씩 읽는다.
                if not line.strip():  # 빈 줄인지 검사한다.
                    continue  # 빈 줄은 무시하고 다음 줄로 넘어간다.
                raw = _parse_json_line(line, self.path)  # JSONL 한 줄을 Python 사전으로 바꾼다.
                if "month" not in raw or "amount" not in raw:  # 필수 항목 두 개가 모두 있는지 검사한다.
                    raise DataFileError("budgets.jsonl 파일에 필수 항목이 없다.", "각 줄에 month와 amount를 모두 넣는다.")  # 필요한 항목을 알린다.
                month = validate_month(str(raw["month"]))  # 저장된 월을 YYYY-MM 형식으로 검사한다.
                amount = validate_amount(raw["amount"])  # 저장된 예산을 양의 정수로 검사한다.
                if month in budgets:  # 같은 월이 이미 읽혔는지 검사한다.
                    message = "budgets.jsonl 파일에 같은 월이 두 번 저장되어 있다."  # 사용자에게 보여 줄 중복 오류 원인을 저장한다.
                    hint = "월별 예산을 한 줄만 남긴다."  # 중복 예산을 해결하는 방법을 저장한다.
                    raise DataFileError(message, hint)  # 저장한 원인과 힌트로 파일 오류를 발생시킨다.
                budgets[month] = amount  # 검사한 월과 금액을 사전에 저장한다.
        return budgets  # 모든 월별 예산을 돌려준다.

    def get(self, month: str) -> Optional[int]:  # 특정 월에 설정된 예산을 찾는다.
        cleaned_month = validate_month(month)  # 찾을 월의 형식을 먼저 검사한다.
        return self._load_all().get(cleaned_month)  # 저장된 금액을 돌려주고 없으면 None을 돌려준다.

    def set(self, month: str, amount: object) -> int:  # 특정 월의 예산을 새로 저장하거나 수정한다.
        cleaned_month = validate_month(month)  # 저장할 월의 형식을 검사한다.
        cleaned_amount = validate_amount(amount)  # 저장할 금액을 양의 정수로 검사한다.
        budgets = self._load_all()  # 현재 저장된 모든 예산을 읽는다.
        budgets[cleaned_month] = cleaned_amount  # 같은 월은 수정하고 새 월은 추가한다.
        sorted_months = sorted(budgets)  # 저장된 월 이름을 오래된 월부터 정렬한다.
        records: List[Dict[str, Any]] = []  # 예산 JSON 객체를 담을 빈 목록을 만든다.
        for saved_month in sorted_months:  # 정렬된 월을 하나씩 꺼낸다.
            saved_amount = budgets[saved_month]  # 현재 월에 저장할 예산 금액을 가져온다.
            record = {"month": saved_month, "amount": saved_amount}  # 월과 금액을 JSON 저장용 사전으로 묶는다.
            records.append(record)  # 만든 예산 사전을 저장 목록에 추가한다.
        _atomic_write_jsonl(self.path, records)  # 전체 예산을 임시 파일에 쓴 뒤 원본과 안전하게 교체한다.
        return cleaned_amount  # 실제로 저장한 금액을 돌려준다.
