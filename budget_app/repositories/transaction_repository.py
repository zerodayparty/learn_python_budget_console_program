# 이 파일은 transactions.jsonl 거래 파일만 읽고 쓰는 저장소를 담당한다.

import os  # os는 추가한 거래를 실제 디스크에 동기화하는 기능을 제공한다.
from pathlib import Path  # Path는 거래 파일 경로를 객체로 다루게 해 준다.
from typing import Any, Dict, Iterator, Optional  # JSON 사전과 반복 반환 및 생략 가능 타입을 표시한다.

from budget_app.constants import TRANSACTIONS_FILENAME  # 거래 저장 파일 이름을 가져온다.
from budget_app.models import Transaction  # 저장하고 읽을 거래 데이터 모델을 가져온다.
from budget_app.repositories.jsonl_storage import atomic_write_jsonl, iter_lines_reverse, json_line, parse_json_line  # 공통 JSONL 파일 도구들을 가져온다.


class TransactionRepository:  # 거래 추가, 조회, 수정, 삭제의 파일 처리를 담당한다.
    def __init__(self, data_dir: Path) -> None:  # 저장 폴더를 받아 거래 파일을 준비한다.
        data_dir.mkdir(parents=True, exist_ok=True)  # 부모 폴더까지 만들고 이미 있으면 그대로 둔다.
        self.path = data_dir / TRANSACTIONS_FILENAME  # 상수로 관리되는 거래 파일 경로를 만든다.
        self.path.touch(exist_ok=True)  # 첫 실행이고 파일이 없으면 빈 파일을 만든다.

    def append(self, transaction: Transaction) -> None:  # 거래 한 건을 파일 마지막에 추가한다.
        with self.path.open("a", encoding="utf-8") as data_file:  # 기존 내용을 유지하는 Append 모드로 파일을 연다.
            data_file.write(json_line(transaction.to_dict()))  # 거래를 JSONL 한 줄로 바꿔 저장한다.
            data_file.flush()  # Python 메모리에 남은 내용을 운영체제로 보낸다.
            os.fsync(data_file.fileno())  # 운영체제 버퍼의 내용도 실제 디스크에 기록하도록 요청한다.

    def iter_oldest(self) -> Iterator[Transaction]:  # 오래된 저장 순서부터 거래를 한 건씩 전달한다.
        with self.path.open("r", encoding="utf-8") as data_file:  # UTF-8 텍스트 읽기 모드로 거래 파일을 연다.
            for line in data_file:  # 파일을 한 줄씩 읽는다.
                if line.strip():  # 현재 줄이 빈 줄이 아닌지 확인한다.
                    yield Transaction.from_dict(parse_json_line(line, self.path))  # JSONL 한 줄을 거래 모델로 바꿔 전달한다.

    def iter_latest(self) -> Iterator[Transaction]:  # 최신 저장 순서부터 거래를 한 건씩 전달한다.
        for line in iter_lines_reverse(self.path):  # 파일 끝에서 시작해 JSONL 한 줄씩 받는다.
            yield Transaction.from_dict(parse_json_line(line, self.path))  # JSONL 한 줄을 거래 모델로 바꿔 전달한다.

    def find_by_id(self, transaction_id: str) -> Optional[Transaction]:  # id가 같은 거래 한 건을 찾는다.
        for transaction in self.iter_latest():  # 최신 거래부터 한 건씩 확인한다.
            if transaction.id == transaction_id:  # 현재 거래 id가 찾는 id와 같은지 확인한다.
                return transaction  # 찾은 거래를 즉시 돌려준다.
        return None  # 끝까지 찾지 못하면 None을 돌려준다.

    def replace(self, replacement: Transaction) -> bool:  # id가 같은 기존 거래를 새 거래로 교체한다.
        if self.find_by_id(replacement.id) is None:  # 교체 대상 거래가 실제로 존재하는지 확인한다.
            return False  # 대상이 없으면 파일을 건드리지 않고 실패를 알린다.

        def replacement_records() -> Iterator[Dict[str, Any]]:  # 교체된 전체 거래를 한 건씩 만드는 내부 제너레이터다.
            for transaction in self.iter_oldest():  # 원래 저장 순서대로 거래를 한 건씩 읽는다.
                if transaction.id == replacement.id:  # 현재 거래가 교체 대상인지 확인한다.
                    yield replacement.to_dict()  # 대상 위치에는 새 거래를 전달한다.
                else:  # 현재 거래가 교체 대상이 아닌 경우다.
                    yield transaction.to_dict()  # 기존 거래를 그대로 전달한다.

        atomic_write_jsonl(self.path, replacement_records())  # 새 전체 내용을 임시 파일에 쓴 뒤 원본과 교체한다.
        return True  # 안전한 파일 교체가 끝났음을 알린다.

    def delete(self, transaction_id: str) -> bool:  # id가 같은 거래 한 건을 삭제한다.
        if self.find_by_id(transaction_id) is None:  # 삭제 대상 거래가 실제로 존재하는지 확인한다.
            return False  # 대상이 없으면 파일을 건드리지 않고 실패를 알린다.

        def remaining_records() -> Iterator[Dict[str, Any]]:  # 삭제 대상을 제외한 데이터를 만드는 내부 제너레이터다.
            for transaction in self.iter_oldest():  # 원래 저장 순서대로 거래를 한 건씩 읽는다.
                if transaction.id != transaction_id:  # 현재 거래가 삭제 대상이 아닌지 확인한다.
                    yield transaction.to_dict()  # 삭제 대상이 아닌 거래만 새 파일로 전달한다.

        atomic_write_jsonl(self.path, remaining_records())  # 남은 거래를 임시 파일에 쓴 뒤 원본과 교체한다.
        return True  # 안전한 삭제가 끝났음을 알린다.
