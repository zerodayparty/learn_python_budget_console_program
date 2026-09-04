# 🟩 파일 기반 가계부 콘솔 프로그램  

Python 표준 라이브러리만 사용하는 JSONL(JSON Lines) 기반 가계부다.  

- 거래 추가·목록·검색·수정·삭제  
- 월별 수입·지출·잔액·카테고리 TOP 요약  
- 월 예산 설정·조회와 예산 초과 경고  
- 카테고리 추가·목록·안전한 삭제  
- UTF-8 CSV 가져오기·내보내기  
- 제너레이터 스트리밍, 데코레이터 오류 처리, 타입 힌트  

<br><br>

## 🟢 1. 실행 환경  

| 항목 | 값 |  
| --- | --- |
| 운영체제 | macOS 포함 모든 Python 지원 운영체제 |  
| Python | 3.10 이상 권장 |  
| 외부 패키지 | 없음 |  
| 실행 위치 | 프로젝트 최상위 폴더 |  

Python 버전 확인:  

```bash
python3 --version  
```

- `Python`은 프로그래밍 언어 이름이다.  
- `--version`은 설치된 버전을 출력하는 옵션이다.  
- 3.10 이상이면 요구사항의 개발 환경을 만족한다.  

현재 프로젝트 폴더로 이동한 뒤 전체 도움말을 확인한다.  

```bash
cd /prj/learn_python_budget_console_program  
python3 -m budget_app --help  
```

- `cd` = Change Directory, 현재 작업 폴더를 변경한다.  
- `-m` = module, 파일 경로 대신 `budget_app` 모듈을 실행한다.  
- `--help`는 사용할 수 있는 명령과 옵션을 출력한다.  

<br><br>

## 🟢 2. 저장 파일  

기본 저장 폴더는 프로젝트 기준 `./data`다. 첫 명령 실행 때 폴더와 파일이 자동 생성된다.  

| 파일 | 저장 내용 | 형식 |  
| --- | --- | --- |
| `data/transactions.jsonl` | 거래 내역 | 한 줄에 거래 JSON 객체 1개 |  
| `data/categories.jsonl` | 카테고리 | 한 줄에 카테고리 JSON 객체 1개 |  
| `data/budgets.jsonl` | 월 예산 | 한 줄에 예산 JSON 객체 1개 |  

첫 실행 때 카테고리 파일이 비어 있으면 다음 기본값을 자동 생성한다.  

`food`, `transport`, `rent`, `salary`, `utilities`, `health`, `leisure`, `other`  

JSONL 저장 예시:  

```json
{"id":"TX-A1B2C3D4E5F6","type":"expense","date":"2026-08-01","amount":15000,"category":"food","memo":"점심","tags":["meal"]}  
```

다른 저장 폴더를 사용하려면 `--data-dir`을 하위 명령 앞에 둔다.  

```bash
python3 -m budget_app --data-dir ./practice_data category list  
```

이 명령은 실제 기본 `data` 대신 `practice_data` 안의 세 파일을 사용한다.  

<br><br>

## 🟢 3. 주요 명령  

### 🟡 거래 추가  

```bash
python3 -m budget_app add  
```

날짜, 타입, 카테고리, 금액, 메모, 태그를 차례로 입력한다. 날짜·타입·금액·카테고리가 잘못되면 올바른 값을 받을 때까지 다시 묻는다.  

### 🟡 최신 거래 목록  

```bash
python3 -m budget_app list --limit 10  
```

- `--limit`은 최대 출력 개수다.  
- 기본값은 10이다.  
- 파일 끝에서부터 한 줄씩 읽는 제너레이터를 사용한다.  

### 🟡 거래 검색  

```bash
python3 -m budget_app search --from 2026-08-01 --to 2026-08-31 --category food --type expense --q 점심 --tag meal  
```

| 옵션 | 뜻 |  
| --- | --- |
| `--from` | 시작 날짜, YYYY-MM-DD |  
| `--to` | 종료 날짜, YYYY-MM-DD |  
| `--category` | 카테고리 일치 |  
| `--type` | `income` 또는 `expense` |  
| `--q` | 메모에 포함된 글자, 대소문자 구분 없음 |  
| `--tag` | 태그 목록에 포함된 정확한 태그 |  

입력한 조건은 모두 동시에 만족해야 한다. 결과는 최신 저장 순서로 출력한다.  

### 🟡 거래 수정  

이 프로젝트의 `update`는 옵션 방식으로 고정했다. 전달한 필드만 바뀌고 나머지는 유지된다.  

```bash
python3 -m budget_app update --id TX-A1B2C3D4E5F6 --amount 18000 --memo "점심 가격 수정" --tags "meal,work"  
```

사용 가능한 수정 옵션:  

`--date`, `--type`, `--category`, `--amount`, `--memo`, `--tags`  

- 하나 이상 반드시 입력한다.  
- 메모나 태그를 지우려면 `--memo ""`, `--tags ""`처럼 빈 문자열을 전달한다.  
- 수정은 임시 파일을 완성한 뒤 `os.replace`로 원본과 교체한다.  

### 🟡 거래 삭제  

```bash
python3 -m budget_app delete --id TX-A1B2C3D4E5F6  
```

없는 id면 원인과 해결 힌트를 출력하고 0이 아닌 종료 코드로 끝난다. 삭제도 임시 파일과 원자적 교체 방식을 사용한다.  

### 🟡 월별 요약  

```bash
python3 -m budget_app summary --month 2026-08 --top 3  
```

- 총수입  
- 총지출  
- 잔액 = 총수입 - 총지출  
- 지출 카테고리 합계 TOP N  
- 예산이 있으면 사용률과 초과 경고  
- 거래가 없으면 `데이터 없음`  

### 🟡 예산 설정·조회  

```bash
python3 -m budget_app budget set --month 2026-08 --amount 500000  
python3 -m budget_app budget get --month 2026-08  
```

예산은 0보다 큰 정수만 저장한다. 같은 월을 다시 설정하면 새 금액으로 수정된다.  

### 🟡 카테고리 관리  

```bash
python3 -m budget_app category list  
python3 -m budget_app category add --name education  
python3 -m budget_app category remove --name education  
```

`--name`을 생략하면 대화형으로 이름을 묻는다. 거래가 사용 중인 카테고리는 삭제하지 않는다.  

<br><br>

## 🟢 4. CSV 가져오기·내보내기  

CSV = Comma-Separated Values, 쉼표로 열을 구분하는 표 파일 형식이다.  

### 🟡 고정 CSV 스키마  

| 열 이름 | 필수 | 값 |  
| --- | --- | --- |
| `date` | Y | YYYY-MM-DD |  
| `type` | Y | `income` 또는 `expense` |  
| `category` | Y | 이미 등록된 카테고리 |  
| `amount` | Y | 0보다 큰 정수 |  
| `memo` | N | 문자열 |  
| `tags` | N | 쉼표로 구분한 문자열 |  

- 문자 인코딩: UTF-8  
- 첫 줄: 헤더 필수  
- 태그에 쉼표가 들어 있으므로 CSV 작성 프로그램은 해당 셀을 큰따옴표로 감싼다.  

예시:  

```csv
date,type,category,amount,memo,tags  
2026-08-01,expense,food,15000,점심,meal  
2026-08-01,income,salary,3000000,8월 급여,work  
```

### 🟡 가져오기  

```bash
python3 -m budget_app import --from ./import.csv  
```

- 정상 줄은 즉시 새 id를 만들어 저장한다.  
- 잘못된 줄은 줄 번호와 이유를 출력하고 건너뛴다.  
- 마지막에 `imported`와 `skipped` 건수를 출력한다.  
- 필수 헤더가 없거나 파일 자체를 열 수 없으면 0이 아닌 종료 코드로 끝난다.  

### 🟡 내보내기  

월 조건:  

```bash
python3 -m budget_app export --out ./export-2026-08.csv --month 2026-08  
```

날짜 범위 조건:  

```bash
python3 -m budget_app export --out ./export-range.csv --from 2026-08-01 --to 2026-08-31  
```

- `--month` 또는 `--from`과 `--to`가 반드시 필요하다.  
- 날짜 범위는 두 옵션을 함께 입력한다.  
- 출력 CSV는 UTF-8이고 헤더를 포함한다.  

<br><br>

## 🟢 5. 코드 구조와 책임  

| 파일 | 책임 |  
| --- | --- |
| `budget_app/models.py` | `Transaction`, `MonthlySummary` 데이터 구조 |  
| `budget_app/validators.py` | 날짜·월·금액·타입·카테고리·태그 검증 |  
| `budget_app/repositories.py` | JSONL 스트리밍, 추가, 임시 파일, 원자적 교체 |  
| `budget_app/services.py` | CRUD, 검색, 요약, 예산, 카테고리, CSV 업무 규칙 |  
| `budget_app/decorators.py` | 공통 오류 출력과 종료 코드 |  
| `budget_app/cli.py` | 명령·옵션 해석, 대화형 입력, 화면 출력 |  
| `budget_app/__main__.py` | `python3 -m budget_app` 시작 지점 |  
| `tests/test_budget_app.py` | 필수 기능 자동 회귀 테스트 |  

CLI = Command-Line Interface, 터미널의 글자 명령으로 프로그램을 조작하는 방식이다.  

CRUD = Create, Read, Update, Delete, 생성·조회·수정·삭제를 뜻한다.  

<br><br>

## 🟢 6. 테스트  

전체 테스트 실행:  

```bash
python3 -m unittest discover -s tests -v  
```

- `unittest` = unit test, Python 표준 테스트 도구다.  
- `discover`는 테스트 파일을 자동으로 찾는다.  
- `-s tests`는 Search 시작 폴더를 `tests`로 지정한다.  
- `-v` = verbose, 테스트 이름과 결과를 자세히 출력한다.  

성공 기준:  

```text
Ran 9 tests  
OK  
```

<br><br>

## 🟢 7. 종료 코드  

명령 실행 직후 다음 명령으로 종료 코드를 확인한다.  

```bash
echo $?  
```

- `echo`는 뒤의 값을 터미널에 출력한다.  
- `$?`는 바로 전에 끝난 명령의 종료 코드다.  

| 종료 코드 | 뜻 |  
| --- | --- |
| `0` | 정상 종료 |  
| `1` | 예상하지 못한 실행 오류 |  
| `2` | 잘못된 입력, 없는 데이터, 충돌, 손상된 데이터 |  
| `3` | 파일 접근·인코딩·CSV 오류 |  
| `130` | 사용자가 Control+C 등으로 입력 중단 |  
