# 이 파일은 프로그램이 다루는 거래와 월별 요약 데이터의 모양을 정의한다.

from dataclasses import dataclass  # dataclass는 데이터 보관용 클래스를 간단하게 만드는 도구다.
from typing import Any, Dict, List, Optional, Tuple  # 각 값의 자료형을 명확히 표시하기 위해 가져온다.

from budget_app.exceptions import DataFileError, ValidationError  # 저장된 거래 모양이 잘못된 경우 사용할 오류들이다.
from budget_app.validators import (  # 저장 데이터를 다시 검사할 함수들을 가져온다.
    normalize_tags,  # 저장된 태그를 문자열 목록으로 정리한다.
    validate_amount,  # 저장된 금액이 양의 정수인지 검사한다.
    validate_category_name,  # 저장된 카테고리 이름을 검사한다.
    validate_date,  # 저장된 날짜의 형식과 실제 날짜를 검사한다.
    validate_transaction_type,  # 저장된 거래 타입을 검사한다.
)  # 저장 데이터 검사 함수 가져오기를 끝낸다.




# ✅
# 객체를 만든 뒤 값이 몰래 바뀌지 않도록 방지하는 거래 데이터 클래스를 선언한다.
@dataclass(frozen=True)  # 만든 뒤 값이 몰래 바뀌지 않는 거래 데이터 클래스를 선언한다.
class Transaction:  # 거래 한 건이 반드시 가져야 할 값을 묶은 클래스다.
    id: str  # 각 거래를 구별하는 유일한 식별자다.
    type: str  # 수입 income 또는 지출 expense를 저장한다.
    date: str  # YYYY-MM-DD 형식의 거래 날짜를 저장한다.
    amount: int  # 0보다 큰 정수 금액을 저장한다.
    category: str  # 등록된 카테고리 이름을 저장한다.
    memo: str  # 선택 입력인 메모를 저장한다.
    tags: List[str]  # 선택 입력인 태그 여러 개를 목록으로 저장한다.

    def to_dict(self) -> Dict[str, Any]:  # 거래를 JSON으로 저장하기 쉬운 사전 모양으로 바꾼다.
        return {  # 각 필드 이름과 실제 값을 한 쌍으로 묶어서 돌려준다.
            "id": self.id,  # 거래 식별자를 id 항목에 넣는다.
            "type": self.type,  # 거래 타입을 type 항목에 넣는다.
            "date": self.date,  # 거래 날짜를 date 항목에 넣는다.
            "amount": self.amount,  # 거래 금액을 amount 항목에 넣는다.
            "category": self.category,  # 카테고리를 category 항목에 넣는다.
            "memo": self.memo,  # 메모를 memo 항목에 넣는다.
            "tags": list(self.tags),  # 원본 보호를 위해 태그 목록을 복사해서 넣는다.
        }  # 거래 사전 만들기를 끝낸다.


    # ✅ 
    # 객체를 미리 만들지 않고도 클래스 이름으로 직접 함수를 호출할 수 있게 만드는 데코레이터
    @classmethod  # 객체가 없어도 Transaction.from_dict 형태로 호출할 수 있게 만든다.
    def from_dict(cls, raw: Dict[str, Any]) -> "Transaction":  # JSON 사전을 검사해서 거래 객체로 바꾼다.
        try:  # 필수 항목 확인과 값 검사를 시도한다.
            transaction_id = str(raw["id"]).strip()  # 필수 id 값을 문자열로 읽는다.
            
            if not transaction_id:  # id가 빈 문자열인지 검사한다.
                raise KeyError("id")  # 빈 id도 필수 항목 누락과 같은 손상으로 처리한다.
 
            return cls(  # 검사를 통과한 값으로 거래 객체를 만든다.
                id=transaction_id,  # 검사한 식별자를 저장한다.
                type=validate_transaction_type(str(raw["type"])),  # 거래 타입을 검사해서 저장한다.
                date=validate_date(str(raw["date"])),  # 거래 날짜를 검사해서 저장한다.
                amount=validate_amount(raw["amount"]),  # 거래 금액을 검사해서 저장한다.
                category=validate_category_name(str(raw["category"])),  # 카테고리를 검사해서 저장한다.
                memo=str(raw.get("memo") or ""),  # 메모가 없으면 빈 문자열로 저장한다.
                tags=normalize_tags(raw.get("tags", [])),  # 태그가 없으면 빈 목록으로 저장한다.
            )  # 거래 객체 만들기를 끝낸다.
        
        except (KeyError, TypeError, ValueError, ValidationError) as error:  # 필수 항목 누락이나 잘못된 값을 잡는다.
            message = "거래 저장 파일의 데이터 형식이 잘못되었다."  # 사용자에게 보여 줄 파일 오류 원인을 저장한다.
            hint = "손상된 줄을 수정하거나 백업 파일로 복구한다."  # 사용자에게 보여 줄 해결 방법을 저장한다.
            raise DataFileError(message, hint) from error  # 저장한 원인과 힌트로 파일 오류를 발생시킨다.



# ✅
# 객체를 만든 뒤 값이 몰래 바뀌지 않도록 방지하는 거래 데이터 클래스를 선언한다.
@dataclass(frozen=True)  # 계산 결과가 나중에 바뀌지 않는 월별 요약 클래스를 선언한다.
class MonthlySummary:  # 한 달의 수입과 지출 계산 결과를 묶은 클래스다.
    month: str  # 계산 대상인 YYYY-MM 형식의 월이다.
    total_income: int  # 해당 월의 모든 수입 합계다.
    total_expense: int  # 해당 월의 모든 지출 합계다.
    category_expenses: List[Tuple[str, int]]  # 지출 카테고리와 합계를 큰 금액 순서로 담는다.
    budget: Optional[int]  # 설정된 예산이며 없으면 None을 저장한다.
    transaction_count: int  # 해당 월에 존재하는 전체 거래 개수다.

    # ✅
    # summary.budget_usage처럼 변수처럼 읽을 수 있는 계산 속성으로 만든다.
    @property  # summary.balance처럼 값처럼 읽을 수 있는 계산 기능으로 만든다.
    def balance(self) -> int:  # 총수입에서 총지출을 뺀 잔액을 계산한다.
        return self.total_income - self.total_expense  # 요구사항의 잔액 계산식을 실행한다.

    # ✅
    # summary.budget_usage처럼 변수처럼 읽을 수 있는 계산 속성으로 만든다.
    @property  # summary.budget_usage처럼 값처럼 읽을 수 있는 계산 기능으로 만든다.
    def budget_usage(self) -> Optional[float]:  # 예산 대비 지출 사용률을 계산한다.
        if self.budget is None:  # 예산이 설정되지 않았는지 검사한다.
            return None  # 계산할 예산이 없다는 뜻으로 None을 돌려준다.
        return self.total_expense / self.budget * 100  # 지출을 예산으로 나누고 백분율로 바꾼다.

    # ✅
    # summary.budget_usage처럼 변수처럼 읽을 수 있는 계산 속성으로 만든다.
    @property  # summary.is_over_budget처럼 값처럼 읽을 수 있는 계산 기능으로 만든다.
    def is_over_budget(self) -> bool:  # 현재 지출이 예산을 초과했는지 계산한다.
        return self.budget is not None and self.total_expense > self.budget  # 예산이 있고 지출이 더 큰 경우만 참이다.
