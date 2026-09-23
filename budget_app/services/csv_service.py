# 이 파일은 거래 CSV 가져오기와 내보내기 업무만 담당한다.

import csv  # csv는 Comma-Separated Values 파일을 읽고 쓰는 Python 표준 도구다.
from pathlib import Path  # Path는 CSV 파일 경로를 객체로 다루게 해 준다.
from typing import List, Optional, Tuple  # 오류 목록과 선택 조건 및 처리 결과 타입을 표시한다.

from budget_app.constants import CSV_COLUMNS, CSV_REQUIRED_COLUMNS, ErrorMessages  # CSV 열 규칙과 오류 메시지를 가져온다.
from budget_app.dtos import CreateTransactionDTO  # CSV 한 줄을 거래 추가 요청으로 묶을 DTO를 가져온다.
from budget_app.exceptions import BudgetAppError, ValidationError  # 행별 입력 오류와 CSV 조건 오류를 알리기 위해 가져온다.
from budget_app.repositories import TransactionRepository  # CSV로 읽고 쓸 거래 저장소를 가져온다.
from budget_app.services.transaction_service import TransactionService  # CSV 가져오기에서 거래 추가 규칙을 재사용하기 위해 가져온다.
from budget_app.validators import validate_date, validate_month  # CSV 내보내기 날짜 조건 검증 함수를 가져온다.


class CsvService:  # CSV 파일과 거래 저장소 사이의 변환 작업을 담당한다.
    def __init__(self, transactions: TransactionRepository, transaction_service: TransactionService) -> None:  # 거래 저장소와 거래 서비스를 받는다.
        self._transactions = transactions  # CSV 내보내기용 거래 저장소를 보관한다.
        self._transaction_service = transaction_service  # CSV 가져오기용 거래 서비스를 보관한다.

    def import_file(self, source: Path) -> Tuple[int, int, List[str]]:  # CSV 거래를 검사하면서 한 건씩 가져온다.
        imported = 0  # 정상적으로 저장한 거래 개수를 0에서 시작한다.
        skipped = 0  # 잘못되어 건너뛴 거래 개수를 0에서 시작한다.
        errors: List[str] = []  # 건너뛴 줄의 이유를 담을 빈 목록을 만든다.
        with source.open("r", encoding="utf-8-sig", newline="") as csv_file:  # UTF-8과 선택적 BOM을 지원하는 읽기 모드로 CSV를 연다.
            reader = csv.DictReader(csv_file)  # 헤더 이름을 열쇠로 사용하는 사전 형태로 한 줄씩 읽는다.
            headers = set(reader.fieldnames or [])  # 파일에 실제로 있는 헤더 이름을 집합으로 만든다.
            missing = CSV_REQUIRED_COLUMNS - headers  # 반드시 필요한데 빠진 헤더를 계산한다.
            if missing:  # 빠진 필수 헤더가 하나 이상 있는지 확인한다.
                missing_text = ", ".join(sorted(missing))  # 빠진 헤더 이름을 읽기 좋은 문자열로 만든다.
                raise ValidationError(*ErrorMessages.csv_missing_headers(missing_text))  # 헤더 누락 오류를 알린다.
            for line_number, row in enumerate(reader, start=2):  # 헤더 다음인 2번 줄부터 번호를 붙여 읽는다.
                try:  # 현재 CSV 행의 검사와 저장을 시도한다.
                    request = CreateTransactionDTO(  # CSV 한 줄을 거래 추가 DTO 한 개로 묶는다.
                        date=row.get("date") or "",  # date 열이 없거나 비었으면 빈 문자열을 전달한다.
                        transaction_type=row.get("type") or "",  # type 열이 없거나 비었으면 빈 문자열을 전달한다.
                        category=row.get("category") or "",  # category 열이 없거나 비었으면 빈 문자열을 전달한다.
                        amount=row.get("amount") or "",  # amount 열이 없거나 비었으면 빈 문자열을 전달한다.
                        memo=row.get("memo") or "",  # 선택 메모가 없으면 빈 문자열을 전달한다.
                        tags=row.get("tags") or "",  # 선택 태그가 없으면 빈 문자열을 전달한다.
                    )  # CSV 행 DTO 만들기를 끝낸다.
                    self._transaction_service.add(request)  # 일반 거래 추가 규칙을 재사용해 거래를 저장한다.
                    imported += 1  # 정상 저장 개수에 1을 더한다.
                except BudgetAppError as error:  # 현재 행의 예상 가능한 입력 오류를 잡는다.
                    skipped += 1  # 건너뛴 개수에 1을 더한다.
                    errors.append(f"line={line_number}: {error.message}")  # 줄 번호와 오류 원인을 기록한다.
        return imported, skipped, errors  # 저장 수, 건너뜀 수, 오류 목록을 함께 돌려준다.

    def export_file(  # 조건에 맞는 거래를 고정 스키마 CSV 파일로 내보낸다.
        self,  # 현재 CSV 서비스 객체 자신을 뜻한다.
        output: Path,  # 새로 만들 CSV 파일 경로다.
        month: Optional[str] = None,  # YYYY-MM 월 조건이며 생략할 수 있다.
        date_from: Optional[str] = None,  # 시작 날짜 조건이며 생략할 수 있다.
        date_to: Optional[str] = None,  # 종료 날짜 조건이며 생략할 수 있다.
    ) -> int:  # 실제로 CSV에 쓴 거래 개수를 돌려준다.
        if not month and not date_from and not date_to:  # 내보내기 조건이 하나도 없는지 확인한다.
            raise ValidationError(*ErrorMessages.EXPORT_CONDITION_REQUIRED)  # 내보내기 조건 필요 오류를 알린다.
        if bool(date_from) != bool(date_to):  # 시작과 종료 날짜 중 하나만 입력했는지 확인한다.
            raise ValidationError(*ErrorMessages.EXPORT_DATE_RANGE_INCOMPLETE)  # 기간 조건 불완전 오류를 알린다.
        checked_month = validate_month(month) if month is not None else None  # 월 조건이 있으면 검사해서 저장한다.
        checked_from = validate_date(date_from) if date_from is not None else None  # 시작 날짜가 있으면 검사해서 저장한다.
        checked_to = validate_date(date_to) if date_to is not None else None  # 종료 날짜가 있으면 검사해서 저장한다.
        if checked_from and checked_to and checked_from > checked_to:  # 시작 날짜가 종료 날짜보다 뒤인지 확인한다.
            raise ValidationError(*ErrorMessages.DATE_RANGE_REVERSED)  # 날짜 범위 역전 오류를 알린다.
        output.parent.mkdir(parents=True, exist_ok=True)  # 출력 파일의 부모 폴더가 없으면 만든다.
        exported = 0  # CSV에 쓴 거래 개수를 0에서 시작한다.
        with output.open("w", encoding="utf-8", newline="") as csv_file:  # UTF-8 CSV 새 파일을 쓰기 모드로 연다.
            writer = csv.DictWriter(csv_file, fieldnames=CSV_COLUMNS)  # 고정 열 순서를 사용하는 CSV 작성기를 만든다.
            writer.writeheader()  # 첫 줄에 고정 CSV 헤더를 쓴다.
            for transaction in self._transactions.iter_latest():  # 최신 거래부터 한 건씩 읽는다.
                if checked_month and not transaction.date.startswith(checked_month + "-"):  # 월 조건과 다른 거래인지 확인한다.
                    continue  # 다른 월의 거래는 건너뛴다.
                if checked_from and transaction.date < checked_from:  # 시작 날짜보다 이전 거래인지 확인한다.
                    continue  # 기간 밖의 거래는 건너뛴다.
                if checked_to and transaction.date > checked_to:  # 종료 날짜보다 이후 거래인지 확인한다.
                    continue  # 기간 밖의 거래는 건너뛴다.
                writer.writerow(  # 요구사항의 여섯 열에 맞춰 거래 한 건을 CSV에 쓴다.
                    {  # 열 이름과 쓸 값을 한 쌍으로 만든다.
                        "date": transaction.date,  # 거래 날짜를 date 열에 쓴다.
                        "type": transaction.type,  # 거래 타입을 type 열에 쓴다.
                        "category": transaction.category,  # 카테고리를 category 열에 쓴다.
                        "amount": transaction.amount,  # 거래 금액을 amount 열에 쓴다.
                        "memo": transaction.memo,  # 메모를 memo 열에 쓴다.
                        "tags": ",".join(transaction.tags),  # 태그 목록을 쉼표 구분 문자열로 바꿔 쓴다.
                    }  # CSV 한 행에 쓸 사전 만들기를 끝낸다.
                )  # CSV 한 행 쓰기를 끝낸다.
                exported += 1  # 내보낸 거래 개수에 1을 더한다.
        return exported  # 실제로 내보낸 거래 개수를 돌려준다.
