# 이 파일은 가계부 필수 기능이 실제로 함께 동작하는지 자동 검증한다.

import csv  # 테스트용 CSV 파일을 요구사항과 같은 형식으로 만들고 읽기 위해 가져온다.
import io  # io는 터미널 출력 내용을 메모리 문자열로 받아 검사하는 도구다.
import tempfile  # tempfile은 실제 사용자 data와 분리된 임시 폴더를 만드는 도구다.
import unittest  # unittest는 Python 표준 자동 테스트 도구다.
from pathlib import Path  # Path는 테스트 파일과 폴더 경로를 다루는 도구다.
from unittest.mock import patch  # patch는 input과 print 출력을 테스트 동안만 바꾸는 도구다.

from budget_app.cli import main  # 실제 CLI(Command-Line Interface) 시작 함수를 검증하기 위해 가져온다.
from budget_app.exceptions import ConflictError, NotFoundError, ValidationError  # 잘못된 작업이 알맞은 오류가 되는지 검사한다.
from budget_app.repositories import BudgetStore, CategoryStore, TransactionRepository  # 세 파일이 실제로 만들어지고 저장되는지 검사한다.
from budget_app.services import BudgetService  # CRUD, 검색, 요약, CSV 규칙을 실제로 실행한다.


class BudgetServiceTest(unittest.TestCase):  # 서비스와 파일 저장 기능을 검증하는 테스트 모음이다.
    def setUp(self) -> None:  # 각 테스트를 시작하기 전에 깨끗한 저장 공간을 준비한다.
        self.temporary_directory = tempfile.TemporaryDirectory()  # 운영체제가 관리하는 새 임시 폴더를 만든다.
        self.data_dir = Path(self.temporary_directory.name) / "data"  # 임시 폴더 안에 테스트용 data 경로를 만든다.
        self.transactions = TransactionRepository(self.data_dir)  # 빈 transactions.jsonl과 거래 저장소를 준비한다.
        self.categories = CategoryStore(self.data_dir)  # 기본 categories.jsonl과 카테고리 저장소를 준비한다.
        self.budgets = BudgetStore(self.data_dir)  # 빈 budgets.jsonl과 예산 저장소를 준비한다.
        self.service = BudgetService(self.transactions, self.categories, self.budgets)  # 세 저장소를 연결한 서비스를 만든다.

    def tearDown(self) -> None:  # 각 테스트가 끝난 뒤 임시 저장 공간을 정리한다.
        self.temporary_directory.cleanup()  # 테스트가 만든 임시 폴더와 파일을 모두 삭제한다.

    def test_first_run_creates_three_persistent_files_and_defaults(self) -> None:  # 첫 실행 저장 정책을 검증한다.
        self.assertTrue((self.data_dir / "transactions.jsonl").is_file())  # 거래 파일이 자동 생성됐는지 확인한다.
        self.assertTrue((self.data_dir / "categories.jsonl").is_file())  # 카테고리 파일이 자동 생성됐는지 확인한다.
        self.assertTrue((self.data_dir / "budgets.jsonl").is_file())  # 예산 파일이 자동 생성됐는지 확인한다.
        self.assertIn("food", self.service.list_categories())  # 첫 실행 기본 카테고리에 food가 있는지 확인한다.
        self.assertIn("salary", self.service.list_categories())  # 첫 실행 기본 카테고리에 salary가 있는지 확인한다.

    def test_add_list_search_update_and_delete(self) -> None:  # 거래 CRUD와 모든 검색 조건을 한 흐름으로 검증한다.
        first = self.service.add_transaction("2026-07-31", "expense", "food", "12000", "점심 식사", "meal,work")  # 첫 지출 거래를 저장한다.
        second = self.service.add_transaction("2026-08-01", "income", "salary", 3000000, "8월 급여", "work")  # 두 번째 수입 거래를 저장한다.
        latest = list(self.service.list_transactions(1))  # 최신 거래 한 건만 제너레이터에서 꺼낸다.
        self.assertEqual(1, len(latest))  # 최신 거래 결과가 정확히 한 건인지 확인한다.
        self.assertEqual(second.id, latest[0].id)  # 나중에 저장한 거래가 가장 먼저 나오는지 확인한다.
        found = list(  # 모든 검색 조건을 동시에 적용한 결과를 목록으로 만든다.
            self.service.search_transactions(  # 기간, 카테고리, 타입, 메모, 태그 검색을 실행한다.
                date_from="2026-07-01",  # 검색 시작 날짜를 지정한다.
                date_to="2026-07-31",  # 검색 종료 날짜를 지정한다.
                category="food",  # food 카테고리만 찾는다.
                transaction_type="expense",  # 지출만 찾는다.
                query="점심",  # 메모에 점심이 포함된 거래만 찾는다.
                tag="meal",  # meal 태그가 포함된 거래만 찾는다.
            )  # 검색 조건 전달을 끝낸다.
        )  # 검색 결과 목록 만들기를 끝낸다.
        self.assertEqual(1, len(found))  # 모든 조건을 만족한 검색 결과가 정확히 한 건인지 확인한다.
        self.assertEqual(first.id, found[0].id)  # 검색 결과가 예상한 첫 거래인지 확인한다.
        updated = self.service.update_transaction(first.id, amount="15000", memo="점심 수정", tags="meal")  # 첫 거래의 일부 필드만 수정한다.
        self.assertEqual(15000, updated.amount)  # 수정한 금액이 새 값인지 확인한다.
        self.assertEqual("food", updated.category)  # 전달하지 않은 카테고리는 기존 값인지 확인한다.
        self.assertEqual("점심 수정", self.transactions.find_by_id(first.id).memo)  # 파일을 다시 읽어 수정된 메모가 영구 저장됐는지 확인한다.
        self.service.delete_transaction(second.id)  # 두 번째 거래를 삭제한다.
        self.assertIsNone(self.transactions.find_by_id(second.id))  # 파일을 다시 읽어 삭제된 거래가 없는지 확인한다.
        with self.assertRaises(NotFoundError):  # 없는 id 삭제가 NotFoundError가 되는지 확인할 문맥을 연다.
            self.service.delete_transaction("TX-NOT-FOUND")  # 실제로 없는 id 삭제를 요청한다.
        temporary_files = list(self.data_dir.glob("*.tmp")) + list(self.data_dir.glob(".*.tmp"))  # 수정·삭제 뒤 남은 임시 파일을 모두 찾는다.
        self.assertEqual([], temporary_files)  # 원자적 교체가 끝난 뒤 찌꺼기 임시 파일이 없는지 확인한다.

    def test_validation_rejects_bad_values(self) -> None:  # 날짜, 금액, 타입, 카테고리 입력 검증을 확인한다.
        with self.assertRaises(ValidationError):  # 존재하지 않는 날짜가 입력 오류가 되는지 확인할 문맥을 연다.
            self.service.add_transaction("2026-02-30", "expense", "food", 1000)  # 2월 30일 거래 저장을 시도한다.
        with self.assertRaises(ValidationError):  # 0원 거래가 입력 오류가 되는지 확인할 문맥을 연다.
            self.service.add_transaction("2026-02-28", "expense", "food", 0)  # 0원 거래 저장을 시도한다.
        with self.assertRaises(ValidationError):  # 허용되지 않은 타입이 입력 오류가 되는지 확인할 문맥을 연다.
            self.service.add_transaction("2026-02-28", "gift", "food", 1000)  # gift 타입 거래 저장을 시도한다.
        with self.assertRaises(ValidationError):  # 등록되지 않은 카테고리가 입력 오류가 되는지 확인할 문맥을 연다.
            self.service.add_transaction("2026-02-28", "expense", "unknown", 1000)  # unknown 카테고리 거래 저장을 시도한다.
        self.assertEqual([], list(self.transactions.iter_latest()))  # 잘못된 거래가 한 건도 파일에 저장되지 않았는지 확인한다.

    def test_summary_budget_and_category_protection(self) -> None:  # 월 요약, 예산 경고, 사용 중 카테고리 보호를 검증한다.
        self.service.add_transaction("2026-08-01", "income", "salary", 1000000)  # 8월 수입을 저장한다.
        self.service.add_transaction("2026-08-02", "expense", "food", 300000)  # 8월 food 지출을 저장한다.
        self.service.add_transaction("2026-08-03", "expense", "rent", 500000)  # 8월 rent 지출을 저장한다.
        self.service.set_budget("2026-08", 700000)  # 지출보다 작은 8월 예산을 저장한다.
        summary = self.service.monthly_summary("2026-08", 2)  # 8월 지출 TOP 2를 포함한 요약을 계산한다.
        self.assertEqual(1000000, summary.total_income)  # 총수입 합계가 맞는지 확인한다.
        self.assertEqual(800000, summary.total_expense)  # 총지출 합계가 맞는지 확인한다.
        self.assertEqual(200000, summary.balance)  # 잔액 계산이 맞는지 확인한다.
        self.assertEqual([("rent", 500000), ("food", 300000)], summary.category_expenses)  # 카테고리가 지출 큰 순서인지 확인한다.
        self.assertTrue(summary.is_over_budget)  # 지출이 예산을 초과했다고 계산하는지 확인한다.
        self.assertAlmostEqual(114.2857, summary.budget_usage, places=3)  # 예산 사용률 계산이 맞는지 소수 셋째 자리까지 확인한다.
        with self.assertRaises(ConflictError):  # 사용 중인 카테고리 삭제가 충돌 오류가 되는지 확인할 문맥을 연다.
            self.service.remove_category("food")  # 거래가 사용하는 food 삭제를 시도한다.
        self.service.add_category("education")  # 사용하지 않는 새 카테고리를 추가한다.
        self.assertIn("education", self.service.list_categories())  # 추가한 카테고리가 목록에 있는지 확인한다.
        self.service.remove_category("education")  # 사용하지 않는 카테고리를 삭제한다.
        self.assertNotIn("education", self.service.list_categories())  # 삭제한 카테고리가 목록에서 사라졌는지 확인한다.

    def test_import_and_export_csv(self) -> None:  # 고정 CSV 스키마와 처리 건수 계산을 검증한다.
        source = Path(self.temporary_directory.name) / "import.csv"  # 가져오기용 CSV 파일 경로를 만든다.
        with source.open("w", encoding="utf-8", newline="") as csv_file:  # 테스트 CSV를 UTF-8 쓰기 모드로 연다.
            writer = csv.DictWriter(csv_file, fieldnames=["date", "type", "category", "amount", "memo", "tags"])  # 고정 스키마 작성기를 만든다.
            writer.writeheader()  # 첫 줄에 헤더를 쓴다.
            writer.writerow({"date": "2026-08-01", "type": "expense", "category": "food", "amount": "5000", "memo": "간식", "tags": "meal"})  # 정상 거래 한 줄을 쓴다.
            invalid_row = {  # 건너뛸 잘못된 CSV 거래 사전을 만든다.
                "date": "잘못된 날짜",  # 날짜 열에 잘못된 문자열을 넣는다.
                "type": "expense",  # 거래 타입 열에는 정상 지출 값을 넣는다.
                "category": "food",  # 카테고리 열에는 등록된 food를 넣는다.
                "amount": "5000",  # 금액 열에는 정상 양의 정수를 넣는다.
                "memo": "실패",  # 메모 열에 이 행의 목적을 나타내는 글자를 넣는다.
                "tags": "",  # 선택 태그 열은 빈 문자열로 둔다.
            }  # 잘못된 CSV 거래 사전 만들기를 끝낸다.
            writer.writerow(invalid_row)  # 날짜가 잘못된 거래 한 줄을 CSV에 쓴다.
        imported, skipped, errors = self.service.import_csv(source)  # CSV 파일을 실제 서비스로 가져온다.
        self.assertEqual((1, 1), (imported, skipped))  # 정상 1건과 건너뜀 1건으로 계산됐는지 확인한다.
        self.assertIn("line=3", errors[0])  # 잘못된 줄 번호가 오류 설명에 포함됐는지 확인한다.
        output = Path(self.temporary_directory.name) / "exports" / "august.csv"  # 내보내기 CSV 경로를 만든다.
        exported = self.service.export_csv(output, month="2026-08")  # 8월 거래만 CSV로 내보낸다.
        self.assertEqual(1, exported)  # 실제로 내보낸 거래가 1건인지 확인한다.
        with output.open("r", encoding="utf-8", newline="") as csv_file:  # 생성된 CSV를 다시 읽기 모드로 연다.
            rows = list(csv.DictReader(csv_file))  # 헤더를 기준으로 모든 CSV 행을 사전 목록으로 읽는다.
        self.assertEqual("간식", rows[0]["memo"])  # 메모가 같은 값으로 내보내졌는지 확인한다.
        self.assertEqual("meal", rows[0]["tags"])  # 태그가 쉼표 구분 문자열로 내보내졌는지 확인한다.
        with self.assertRaises(ValidationError):  # 조건 없는 export가 입력 오류가 되는지 확인할 문맥을 연다.
            self.service.export_csv(output)  # 월과 기간 없이 내보내기를 시도한다.

    def test_summary_reports_empty_month(self) -> None:  # 거래 없는 월도 오류 없이 명확한 결과를 만드는지 검증한다.
        self.service.set_budget("2026-09", 500000)  # 거래가 없는 9월에 예산만 저장한다.
        summary = self.service.monthly_summary("2026-09", 3)  # 아무 거래도 없는 9월 요약을 계산한다.
        self.assertEqual(0, summary.transaction_count)  # 거래 개수가 0인지 확인한다.
        self.assertEqual(0, summary.total_income)  # 총수입이 0인지 확인한다.
        self.assertEqual(0, summary.total_expense)  # 총지출이 0인지 확인한다.
        self.assertEqual(500000, summary.budget)  # 거래가 없어도 저장한 예산을 조회하는지 확인한다.
        self.assertEqual(0.0, summary.budget_usage)  # 거래가 없으면 예산 사용률이 0%인지 확인한다.


class BudgetCliTest(unittest.TestCase):  # 실제 명령어 해석, 대화형 입력, 종료 코드를 검증하는 테스트 모음이다.
    def setUp(self) -> None:  # 각 CLI 테스트 전에 깨끗한 임시 저장 공간을 준비한다.
        self.temporary_directory = tempfile.TemporaryDirectory()  # 운영체제가 관리하는 새 임시 폴더를 만든다.
        self.data_dir = Path(self.temporary_directory.name) / "cli-data"  # CLI가 사용할 임시 data 경로를 만든다.

    def tearDown(self) -> None:  # 각 CLI 테스트가 끝난 뒤 임시 저장 공간을 정리한다.
        self.temporary_directory.cleanup()  # 테스트가 만든 임시 폴더와 파일을 모두 삭제한다.

    def test_interactive_add_then_list(self) -> None:  # add 대화형 입력과 list 최신순 출력을 함께 검증한다.
        answers = ["2026-08-01", "expense", "food", "15000", "점심", "meal"]  # input이 차례로 돌려줄 사용자 답변을 준비한다.
        add_output = io.StringIO()  # add 화면 출력을 메모리에 받을 빈 문자열 통로를 만든다.
        with patch("builtins.input", side_effect=answers), patch("sys.stdout", add_output):  # 실제 키보드와 화면을 테스트 값으로 잠시 바꾼다.
            add_code = main(["--data-dir", str(self.data_dir), "add"])  # 실제 add 명령을 실행한다.
        self.assertEqual(0, add_code)  # add가 정상 종료 코드 0을 돌려줬는지 확인한다.
        self.assertIn("[저장 완료] id=TX-", add_output.getvalue())  # 생성된 id가 성공 메시지에 포함됐는지 확인한다.
        list_output = io.StringIO()  # list 화면 출력을 메모리에 받을 빈 문자열 통로를 만든다.
        with patch("sys.stdout", list_output):  # 실제 화면을 테스트 문자열 통로로 잠시 바꾼다.
            list_code = main(["--data-dir", str(self.data_dir), "list", "--limit", "1"])  # 실제 list 명령을 실행한다.
        self.assertEqual(0, list_code)  # list가 정상 종료 코드 0을 돌려줬는지 확인한다.
        self.assertIn("2026-08-01 | expense | food | 15000 | 점심 | meal", list_output.getvalue())  # 저장한 모든 주요 필드가 출력됐는지 확인한다.

    def test_error_has_reason_hint_and_nonzero_exit_code(self) -> None:  # 오류 화면에 원인, 힌트, 실패 종료 코드가 있는지 검증한다.
        output = io.StringIO()  # 오류 화면 출력을 메모리에 받을 빈 문자열 통로를 만든다.
        with patch("sys.stdout", output):  # 실제 화면을 테스트 문자열 통로로 잠시 바꾼다.
            exit_code = main(["--data-dir", str(self.data_dir), "delete", "--id", "TX-NOT-FOUND"])  # 없는 id 삭제 명령을 실행한다.
        self.assertNotEqual(0, exit_code)  # 오류 종료 코드가 0이 아닌지 확인한다.
        self.assertIn("[오류]", output.getvalue())  # 오류 원인 표시가 출력됐는지 확인한다.
        self.assertIn("[힌트]", output.getvalue())  # 해결 힌트 표시가 출력됐는지 확인한다.
        self.assertNotIn("Traceback", output.getvalue())  # 스택트레이스가 사용자 화면에 없는지 확인한다.

    def test_empty_month_summary_prints_saved_budget(self) -> None:  # 거래 없는 달에도 저장된 예산을 출력하는지 검증한다.
        budget_output = io.StringIO()  # budget set 화면 출력을 받을 빈 문자열 통로를 만든다.
        with patch("sys.stdout", budget_output):  # 실제 화면을 테스트 문자열 통로로 잠시 바꾼다.
            budget_code = main(  # 실제 budget set 명령을 실행하고 종료 코드를 받는다.
                [  # 명령에 전달할 문자열 인자를 순서대로 만든다.
                    "--data-dir",  # 다음 값이 테스트 저장 폴더임을 알리는 옵션이다.
                    str(self.data_dir),  # 임시 저장 폴더 경로를 문자열로 전달한다.
                    "budget",  # 예산 관리 명령을 선택한다.
                    "set",  # 예산 저장 작업을 선택한다.
                    "--month",  # 다음 값이 예산 월임을 알리는 옵션이다.
                    "2026-09",  # 거래가 없는 2026년 9월을 전달한다.
                    "--amount",  # 다음 값이 예산 금액임을 알리는 옵션이다.
                    "500000",  # 50만원 예산을 문자열로 전달한다.
                ]  # budget set 명령 인자 만들기를 끝낸다.
            )  # budget set 명령 실행을 끝낸다.
        self.assertEqual(0, budget_code)  # 예산 저장이 정상 종료 코드 0인지 확인한다.
        summary_output = io.StringIO()  # summary 화면 출력을 받을 빈 문자열 통로를 만든다.
        with patch("sys.stdout", summary_output):  # 실제 화면을 테스트 문자열 통로로 잠시 바꾼다.
            summary_code = main(  # 실제 summary 명령을 실행하고 종료 코드를 받는다.
                [  # 명령에 전달할 문자열 인자를 순서대로 만든다.
                    "--data-dir",  # 다음 값이 테스트 저장 폴더임을 알리는 옵션이다.
                    str(self.data_dir),  # 예산과 같은 임시 저장 폴더를 전달한다.
                    "summary",  # 월별 요약 명령을 선택한다.
                    "--month",  # 다음 값이 조회할 월임을 알리는 옵션이다.
                    "2026-09",  # 거래 없이 예산만 있는 2026년 9월을 전달한다.
                ]  # summary 명령 인자 만들기를 끝낸다.
            )  # summary 명령 실행을 끝낸다.
        printed = summary_output.getvalue()  # 화면에 출력된 전체 문자열을 가져온다.
        self.assertEqual(0, summary_code)  # 요약 조회가 정상 종료 코드 0인지 확인한다.
        self.assertIn("2026-09: 데이터 없음", printed)  # 거래가 없다는 안내가 출력됐는지 확인한다.
        self.assertIn("예산: 500000원 (사용률 0.0%)", printed)  # 저장한 예산과 0% 사용률이 출력됐는지 확인한다.

    def test_interactive_update_flow(self) -> None:  # 대화형 거래 수정(안 B) 흐름을 검증한다.
        # 먼저 수정 대상이 될 거래 한 건을 등록한다.
        add_inputs = ["2026-08-01", "expense", "food", "10000", "점심", "work"]  # 등록 시 input으로 넘길 값들이다.
        with patch("builtins.input", side_effect=add_inputs), patch("sys.stdout", io.StringIO()):  # 키보드와 화면을 임시 통로로 대체한다.
            main(["--data-dir", str(self.data_dir), "add"])  # 거래 등록 명령을 실행한다.
        repo = TransactionRepository(self.data_dir)  # 등록된 거래 id를 확인하기 위해 저장소를 연다.
        saved_list = list(repo.iter_latest())  # 저장된 전체 거래를 최신순으로 읽는다.
        self.assertEqual(1, len(saved_list))  # 거래가 정확히 한 건 등록되었는지 확인한다.
        target_id = saved_list[0].id  # 생성된 실제 거래 고유 id를 가져온다.
        # 거래 수정 시 전달할 대화형 답변들을 순서대로 준비한다.
        update_inputs = [  # id, 날짜유지, 타입유지, 카테고리유지, 새금액, 새메모, 태그유지 순서다.
            target_id,  # 방금 생성된 실제 거래의 id를 입력한다.
            "",  # 날짜 변경 없이 엔터를 누른다.
            "",  # 타입 변경 없이 엔터를 누른다.
            "",  # 카테고리 변경 없이 엔터를 누른다.
            "25000",  # 금액을 25000원으로 새로 입력한다.
            "수정된 점심",  # 메모를 새 내용으로 입력한다.
            "",  # 태그 변경 없이 엔터를 누른다.
        ]  # 대화형 수정 답변 목록 만들기를 끝낸다.
        update_output = io.StringIO()  # 화면 출력을 메모리에 담을 객체를 만든다.
        with patch("builtins.input", side_effect=update_inputs), patch("sys.stdout", update_output):  # 대화형 입출력을 연결한다.
            exit_code = main(["--data-dir", str(self.data_dir), "update"])  # 대화형 update 명령을 실행한다.
        self.assertEqual(0, exit_code)  # 정상 종료 코드 0이 반환되었는지 확인한다.
        self.assertIn(f"[수정 완료] id={target_id}", update_output.getvalue())  # 수정 완료 메시지가 화면에 나왔는지 확인한다.
        updated_tx = repo.find_by_id(target_id)  # 수정된 거래를 id로 가져온다.
        self.assertEqual(25000, updated_tx.amount)  # 변경한 금액이 25000원으로 영구 저장되었는지 검증한다.
        self.assertEqual("수정된 점심", updated_tx.memo)  # 변경한 메모가 영구 저장되었는지 검증한다.
        self.assertEqual("2026-08-01", updated_tx.date)  # 엔터로 유지한 기존 날짜가 그대로인지 검증한다.

    def test_interactive_console_quit(self) -> None:  # 하위 명령 없이 진입한 대화형 콘솔에서 정상 종료(q)를 검증한다.
        console_output = io.StringIO()  # 콘솔 메뉴 화면 출력을 담을 통로를 준비한다.
        with patch("builtins.input", side_effect=["q"]), patch("sys.stdout", console_output):  # q를 입력받고 화면을 가로챈다.
            exit_code = main(["--data-dir", str(self.data_dir)])  # 하위 명령 없이 데이터 폴더만 주고 실행한다.
        self.assertEqual(0, exit_code)  # 정상 종료 코드 0을 돌려주었는지 확인한다.
        printed = console_output.getvalue()  # 화면 출력 전체를 가져온다.
        self.assertIn("대화형 콘솔 모드", printed)  # 대화형 콘솔 환영 헤더가 출력되었는지 확인한다.
        self.assertIn("가계부 메인 메뉴", printed)  # 메뉴 목록이 출력되었는지 확인한다.
        self.assertIn("가계부 프로그램을 종료한다", printed)  # 종료 인사가 출력되었는지 확인한다.

    def test_interactive_console_loop_add_and_list(self) -> None:  # 대화형 콘솔 안에서 연속으로 추가 후 목록을 조회하는 전체 루프를 검증한다.
        user_inputs = [  # 콘솔 루프 동안 순서대로 키보드에 입력할 문자열들이다.
            "1",  # 메인 메뉴에서 1번(거래 추가)을 선택한다.
            "2026-08-15",  # 날짜를 입력한다.
            "expense",  # 지출 타입을 입력한다.
            "food",  # food 카테고리를 입력한다.
            "9000",  # 금액을 입력한다.
            "김밥세트",  # 메모를 입력한다.
            "lunch",  # 태그를 입력한다.
            "2",  # 메인 메뉴에서 2번(최근 거래 목록)을 선택한다.
            "5",  # 목록 출력 개수로 5를 입력한다.
            "q",  # 모든 작업을 마치고 q로 프로그램을 종료한다.
        ]  # 입력 시나리오 구성을 끝낸다.
        console_output = io.StringIO()  # 화면 출력을 담을 통로를 준비한다.
        with patch("builtins.input", side_effect=user_inputs), patch("sys.stdout", console_output):  # 키보드와 화면을 대체한다.
            exit_code = main(["--data-dir", str(self.data_dir)])  # 대화형 콘솔을 실행한다.
        self.assertEqual(0, exit_code)  # 연속 작업 후 정상 종료 코드 0을 돌려주었는지 확인한다.
        printed = console_output.getvalue()  # 화면 전체 출력을 가져온다.
        self.assertIn("[저장 완료] id=TX-", printed)  # 콘솔 내에서 거래 추가 성공 메시지가 나왔는지 확인한다.
        self.assertIn("2026-08-15 | expense | food | 9000 | 김밥세트 | lunch", printed)  # 콘솔 내에서 목록 조회가 되었는지 확인한다.
        self.assertIn("가계부 프로그램을 종료한다", printed)  # 마지막에 정상 종료 메시지가 나왔는지 확인한다.


if __name__ == "__main__":  # 이 테스트 파일을 직접 실행했는지 확인한다.
    unittest.main()  # 현재 파일의 모든 test_ 메서드를 찾아 실행한다.
