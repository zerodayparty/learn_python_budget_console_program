# 🟩 DTO 적용과 계층별 책임 분리  

## 🟢 먼저 결론  

- DTO는 `Data Transfer Object`(데이터 전송 객체)의 줄임말이다.  
- Python에 `DTO`라는 전용 키워드는 없다.  
- 그러나 Python에서도 `class`, `dataclass`로 DTO 패턴을 구현한다.  
- 수정 전 코드의 6~7개 매개변수는 `Long Parameter List`(긴 매개변수 목록) 문제가 맞다.  
- 서비스가 검증 함수를 호출했다는 사실만으로 설계가 틀렸다고 할 수는 없다.  
- 진짜 문제는 입력 형식 검증, 업무 규칙, 저장, 검색 조건 판단이 큰 메서드 안에 섞여 있었다는 점이다.  

<br><br>

## 🟢 수정 전의 실제 문제  

| 구분 | 수정 전 | 문제 |  
| :--- | :--- | :--- |
| 거래 추가 | 서비스에 6개 값 전달 | 인자 순서를 바꾸면 실수하기 쉽다. |  
| 거래 검색 | 서비스에 6개 조건 전달 | 선택 값 검사와 필터 판단이 서비스에 모였다. |  
| 거래 수정 | 서비스에 7개 값 전달 | 생략 값 판단과 검증과 교체가 한 메서드에 모였다. |  
| 조건문 | `if`가 여러 개 존재 | `if` 개수 자체가 오류는 아니지만 책임이 모였다는 신호였다. |  

<br><br>

## 🟢 수정한 구조  

| 계층 | 담당 책임 | 실제 파일 |  
| :--- | :--- | :--- |
| CLI | 키보드와 명령줄 값을 받고 DTO를 만듦 | `budget_app/cli/app.py`, `budget_app/cli/interactive.py`, `budget_app/cli/prompt.py` |  
| DTO | 여러 입력을 한 객체로 묶고 형식을 검증·정리 | `budget_app/dtos.py` |  
| Service | 등록 카테고리, 거래 존재, 저장 같은 업무 규칙 처리 | `budget_app/services/` |
| Repository | JSONL 파일 읽기와 쓰기 | `budget_app/repositories/` |

<br><br>

## 🟢 기존 진행 방식에서 변경된 방식  

| 비교 항목 | 기존 진행 방식 | 변경된 진행 방식 | 변경한 이유 |  
| :--- | :--- | :--- | :--- |
| CLI 입력 수신 | CLI가 날짜, 타입, 카테고리, 금액, 메모, 태그를 각각의 변수로 받았다. | CLI가 각 값을 받은 뒤 목적에 맞는 DTO 객체를 만든다. | 서비스로 넘기기 전에 관련 값을 하나의 요청으로 묶기 위해서다. |  
| Service 호출 방식 | `add_transaction(date, type, category, amount, memo, tags)`처럼 6~7개 값을 낱개로 전달했다. | `add_transaction(request)`처럼 DTO 하나를 전달한다. | 인자 순서 실수와 긴 매개변수 목록을 없애기 위해서다. |  
| 입력 형식 검증 | Service 메서드가 `validate_date()`, `validate_amount()` 등을 직접 호출했다. | DTO가 생성될 때 `validators/`의 함수를 사용해 입력 형식을 검증한다. | Service가 입력 문자열 정리보다 업무 규칙에 집중하게 하기 위해서다. |
| 입력값 정리 | Service가 공백 제거, 금액 정수 변환, 태그 중복 제거를 담당했다. | DTO가 공백을 제거하고 금액과 태그를 정규화한다. | Service가 정리된 값만 받도록 보장하기 위해서다. |  
| 업무 규칙 검증 | 입력 형식 검증과 업무 규칙 검증이 Service에 섞여 있었다. | 등록된 카테고리인지, 거래가 존재하는지 같은 업무 규칙만 Service가 검사한다. | 입력 형식과 프로그램 업무 규칙은 서로 다른 책임이기 때문이다. |  
| 거래 검색 | Service 메서드가 선택 값 검증과 여섯 개의 검색 조건 비교를 모두 담당했다. | `SearchTransactionsDTO`가 조건을 검증·보관하고, Service의 `_matches_search()`가 거래와 조건을 비교한다. | 검색 조건 데이터와 검색 판단 로직을 구분하기 위해서다. |  
| 거래 수정 | Service가 일곱 개 값을 받고, 값 생략 여부와 유효성을 모두 판단했다. | `UpdateTransactionDTO`가 수정할 값을 묶고 검증하며, Service는 거래 존재와 카테고리 등록 여부를 확인한 뒤 교체한다. | 수정 요청 정리와 실제 수정 작업을 나누기 위해서다. |  
| CSV 가져오기 | CSV 한 줄의 값을 `add_transaction()`에 낱개로 넘겼다. | CSV 한 줄로 `CreateTransactionDTO`를 만든 뒤 Service에 전달한다. | CLI와 CSV가 같은 DTO 규칙을 사용하도록 만들기 위해서다. |  
| 변경 영향 범위 | 필드가 추가되면 Service 메서드와 여러 호출부의 매개변수를 함께 바꿔야 했다. | 데이터 구조와 검증 변경을 해당 DTO에 먼저 반영할 수 있다. | 관련 변경을 한 곳에 모아 수정 누락 가능성을 줄이기 위해서다. |  

<br><br>

## 🟢 전체 진행 순서 비교  

- 대표적인 변경 사항  
    1. 각각의 변수로 관리하는 것이 아닌 객체로 관리하기  
    2. service의 과도한 업무비중 분산  


| 단계 | 기존 진행 순서 | 변경된 진행 순서 |  
| :--- | :--- | :--- |
| 1 | CLI가 여러 입력값을 받는다. | CLI가 여러 입력값을 받는다. |  
| 2 | CLI가 6~7개 값을 Service에 바로 넘긴다. | CLI가 목적에 맞는 DTO를 만든다. |  
| 3 | Service가 각 값의 형식을 검증하고 정리한다. | DTO가 `validators/`를 사용해 각 값을 검증하고 정리한다. |
| 4 | Service가 업무 규칙을 검증한다. | CLI가 완성된 DTO 하나를 Service에 넘긴다. |  
| 5 | Service가 `Transaction`을 만든다. | Service가 DTO의 값으로 업무 규칙을 검증한다. |  
| 6 | Service가 Repository에 저장을 요청한다. | Service가 `Transaction`을 만든다. |  
| 7 | Repository가 JSONL 파일에 저장한다. | Service가 Repository에 저장을 요청한다. |  
| 8 | 해당 없음 | Repository가 JSONL 파일에 저장한다. |  

<br><br>

## 🟢 추가한 DTO 세 개  

### 🟡 `CreateTransactionDTO`  

- 날짜, 타입, 카테고리, 금액, 메모, 태그를 한 객체로 묶는다.  
- 날짜와 타입을 검사한다.  
- 문자열 금액을 정수로 바꾼다.  
- 메모 공백을 정리하고 중복 태그를 제거한다.  

### 🟡 `SearchTransactionsDTO`  

- 여섯 검색 조건을 하나로 묶는다.  
- 시작일이 종료일보다 늦으면 DTO 생성 시점에 오류를 낸다.  
- DTO는 검색 조건만 보관하고, 서비스의 `_matches_search()`가 거래 한 건과 조건을 비교한다.  

### 🟡 `UpdateTransactionDTO`  

- 거래 ID와 수정할 값을 하나로 묶는다.  
- 전달된 값만 검증하고, `None`은 기존 값 유지로 해석한다.  
- `has_changes`로 실제 수정할 필드가 있는지 확인한다.  

<br><br>

## 🟢 검증을 DTO로 전부 옮겨야 하나  

- 아니다. 검증은 성격에 따라 나눈다.  

| 검증 종류 | 예시 | 담당 |  
| :--- | :--- | :--- |
| 입력 형식 검증 | 날짜 형식, 양의 정수 금액, 허용된 타입 | DTO와 `validators/` |
| 업무 규칙 검증 | 실제 등록된 카테고리인지, 수정할 거래가 존재하는지 | Service |  
| 저장 규칙 | JSONL 추가, 교체, 삭제 | Repository |  

<br><br>

## 🟢 핵심 코드 흐름  

```python
# 여섯 입력값을 검증하는 DTO 한 개로 묶는다.  
request = CreateTransactionDTO(date, transaction_type, category, amount, memo, tags)  
# 서비스에는 낱개 값 대신 DTO 한 개만 전달한다.  
created = service.add_transaction(request)  
```
