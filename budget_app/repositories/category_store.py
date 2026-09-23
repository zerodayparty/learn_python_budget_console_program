# 이 파일은 categories.jsonl 카테고리 파일만 읽고 쓰는 저장소를 담당한다.

import os  # os는 추가한 카테고리를 실제 디스크에 동기화하는 기능을 제공한다.
from pathlib import Path  # Path는 카테고리 파일 경로를 객체로 다루게 해 준다.
from typing import Any, Dict, List  # JSON 사전과 카테고리 목록 타입을 표시한다.

from budget_app.constants import CATEGORIES_FILENAME, DEFAULT_CATEGORIES, ErrorMessages  # 카테고리 파일 이름, 기본값, 오류 메시지를 가져온다.
from budget_app.exceptions import ConflictError, DataFileError  # 중복과 손상된 파일 오류를 알리기 위해 가져온다.
from budget_app.repositories.jsonl_storage import atomic_write_jsonl, json_line, parse_json_line  # 공통 JSONL 파일 도구들을 가져온다.
from budget_app.validators import validate_category_name  # 카테고리 이름 검증 함수를 가져온다.


class CategoryStore:  # 카테고리 목록의 파일 저장과 조회를 담당한다.
    def __init__(self, data_dir: Path) -> None:  # 저장 폴더를 받아 카테고리 파일을 준비한다.
        data_dir.mkdir(parents=True, exist_ok=True)  # 부모 폴더까지 만들고 이미 있으면 그대로 둔다.
        self.path = data_dir / CATEGORIES_FILENAME  # 상수로 관리되는 카테고리 파일 경로를 만든다.
        self.path.touch(exist_ok=True)  # 첫 실행이고 파일이 없으면 빈 파일을 만든다.
        if self.path.stat().st_size == 0:  # 카테고리 파일이 비어 있는 첫 실행인지 확인한다.
            default_records = [{"name": name} for name in DEFAULT_CATEGORIES]  # 기본 카테고리를 JSON 저장용 사전 목록으로 만든다.
            atomic_write_jsonl(self.path, default_records)  # 기본 카테고리 목록을 안전하게 저장한다.

    def list_all(self) -> List[str]:  # 저장된 모든 카테고리를 정렬해서 돌려준다.
        categories: List[str] = []  # 읽은 카테고리를 담을 빈 목록을 만든다.
        with self.path.open("r", encoding="utf-8") as data_file:  # 카테고리 파일을 UTF-8 읽기 모드로 연다.
            for line in data_file:  # 파일을 한 줄씩 읽는다.
                if not line.strip():  # 현재 줄이 빈 줄인지 확인한다.
                    continue  # 빈 줄은 무시하고 다음 줄로 넘어간다.
                raw = parse_json_line(line, self.path)  # JSONL 한 줄을 Python 사전으로 바꾼다.
                if "name" not in raw:  # 필수 name 항목이 존재하는지 확인한다.
                    raise DataFileError(*ErrorMessages.CATEGORY_RECORD_INVALID)  # 카테고리 레코드 오류를 알린다.
                name = validate_category_name(str(raw["name"]))  # 저장된 카테고리 이름을 검사한다.
                if name in categories:  # 같은 이름을 이미 읽었는지 확인한다.
                    raise DataFileError(*ErrorMessages.CATEGORY_DUPLICATE_IN_FILE)  # 파일 내부 중복 오류를 알린다.
                categories.append(name)  # 검사한 이름을 결과 목록에 추가한다.
        return sorted(categories)  # 이름을 가나다와 알파벳 순서로 정렬해 돌려준다.

    def exists(self, name: str) -> bool:  # 특정 카테고리가 등록되어 있는지 확인한다.
        return name in self.list_all()  # 전체 목록에 같은 이름이 있는지 참 또는 거짓으로 돌려준다.

    def add(self, name: str) -> None:  # 새 카테고리 한 개를 저장한다.
        cleaned = validate_category_name(name)  # 저장 전에 카테고리 이름을 검사하고 정리한다.
        if self.exists(cleaned):  # 같은 이름이 이미 등록되어 있는지 확인한다.
            raise ConflictError(*ErrorMessages.category_already_exists(cleaned))  # 중복 카테고리 오류를 알린다.
        with self.path.open("a", encoding="utf-8") as data_file:  # 기존 내용을 유지하는 Append 모드로 파일을 연다.
            data_file.write(json_line({"name": cleaned}))  # 카테고리 객체를 JSONL 한 줄로 저장한다.
            data_file.flush()  # Python 메모리에 남은 내용을 운영체제로 보낸다.
            os.fsync(data_file.fileno())  # 운영체제 버퍼의 내용도 실제 디스크에 기록하도록 요청한다.

    def remove(self, name: str) -> bool:  # 카테고리 한 개를 파일에서 삭제한다.
        cleaned = validate_category_name(name)  # 삭제할 카테고리 이름을 검사하고 정리한다.
        categories = self.list_all()  # 현재 카테고리를 모두 읽는다.
        if cleaned not in categories:  # 삭제할 이름이 등록되어 있는지 확인한다.
            return False  # 등록되지 않은 이름이면 파일을 건드리지 않는다.
        remaining_records: List[Dict[str, Any]] = []  # 삭제 후 남길 카테고리 사전을 담을 목록을 만든다.
        for current in categories:  # 현재 카테고리 이름을 하나씩 꺼낸다.
            if current != cleaned:  # 현재 이름이 삭제 대상과 다른지 확인한다.
                remaining_records.append({"name": current})  # 삭제 대상이 아닌 이름만 저장 목록에 추가한다.
        atomic_write_jsonl(self.path, remaining_records)  # 삭제 대상이 빠진 목록으로 원본 파일을 교체한다.
        return True  # 카테고리 삭제가 끝났음을 알린다.
