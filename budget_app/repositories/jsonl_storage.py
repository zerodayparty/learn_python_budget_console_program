# 이 파일은 모든 저장소가 함께 사용하는 JSONL 읽기와 안전한 파일 교체 기능을 담당한다.

import json  # json은 Python 데이터를 JSON 문자열로 바꾸거나 JSON 문자열을 읽는 표준 도구다.
import os  # os는 파일 위치 이동과 디스크 동기화 기능을 제공한다.
import tempfile  # tempfile은 안전한 임시 파일을 만드는 표준 도구다.
from pathlib import Path  # Path는 파일 경로를 객체로 다루게 해 준다.
from typing import Any, Dict, Iterable, Iterator, Optional  # JSON 자료형과 반복 가능한 반환 타입을 표시한다.

from budget_app.constants import ErrorMessages  # 파일 손상 오류 메시지를 가져온다.
from budget_app.exceptions import DataFileError  # 잘못된 JSONL 데이터를 사용자용 오류로 바꾸기 위해 가져온다.


def json_line(record: Dict[str, Any]) -> str:  # 사전 한 개를 JSONL 한 줄로 바꾼다.
    return json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"  # 한글을 유지하고 마지막에 줄바꿈을 붙인다.


def atomic_write_jsonl(path: Path, records: Iterable[Dict[str, Any]]) -> None:  # 여러 데이터를 임시 파일에 쓴 뒤 원본과 한 번에 교체한다.
    temporary_path: Optional[Path] = None  # 작업 실패 시 정리할 임시 파일 경로를 준비한다.
    try:  # 임시 파일 생성부터 원본 교체까지 안전하게 시도한다.
        with tempfile.NamedTemporaryFile(  # 원본과 같은 폴더에 이름이 겹치지 않는 임시 파일을 만든다.
            mode="w",  # 텍스트를 새로 쓰는 모드로 연다.
            encoding="utf-8",  # 모든 글자를 UTF-8 형식으로 저장한다.
            dir=str(path.parent),  # 원자적 교체를 위해 원본과 같은 폴더를 사용한다.
            prefix=f".{path.name}.",  # 임시 파일임을 알 수 있는 이름 앞부분을 지정한다.
            suffix=".tmp",  # Temporary의 줄임말인 tmp 확장자를 붙인다.
            delete=False,  # 파일을 닫은 뒤 교체에 사용하도록 자동 삭제를 끈다.
        ) as temporary_file:  # 생성된 임시 파일을 이 블록에서 사용한다.
            temporary_path = Path(temporary_file.name)  # 나중에 교체하거나 삭제할 수 있도록 경로를 저장한다.
            for record in records:  # 저장할 데이터를 한 건씩 꺼낸다.
                temporary_file.write(json_line(record))  # 현재 데이터를 JSONL 한 줄로 임시 파일에 쓴다.
            temporary_file.flush()  # Python 메모리에 남은 내용을 운영체제로 보낸다.
            os.fsync(temporary_file.fileno())  # 운영체제 버퍼의 내용도 실제 디스크에 기록하도록 요청한다.
        os.replace(temporary_path, path)  # 임시 파일을 원본 경로로 원자적으로 교체한다.
        temporary_path = None  # 교체가 끝났으므로 정리할 임시 파일이 없다고 표시한다.
    finally:  # 성공과 실패에 상관없이 남은 임시 파일을 정리한다.
        if temporary_path is not None and temporary_path.exists():  # 교체되지 않은 임시 파일이 남았는지 확인한다.
            temporary_path.unlink()  # 실패 과정에서 남은 임시 파일을 삭제한다.


def parse_json_line(line: str, path: Path) -> Dict[str, Any]:  # JSONL 한 줄을 Python 사전으로 바꾼다.
    try:  # JSON 문자열 해석을 시도한다.
        parsed = json.loads(line)  # JSON 문자열을 Python 값으로 변환한다.
    except (UnicodeDecodeError, json.JSONDecodeError) as error:  # 문자 인코딩 또는 JSON 문법 오류를 잡는다.
        raise DataFileError(*ErrorMessages.FILE_ENCODING_ERROR) from error  # 저장 파일 손상 오류로 바꿔 알린다.
    if not isinstance(parsed, dict):  # 해석 결과가 JSON 객체인 사전인지 확인한다.
        raise DataFileError(*ErrorMessages.JSON_FORMAT_INVALID)  # JSON 객체 모양 오류를 알린다.
    return parsed  # 검사한 사전을 돌려준다.


def iter_lines_reverse(path: Path, block_size: int = 8192) -> Iterator[str]:  # 큰 파일을 통째로 읽지 않고 마지막 줄부터 전달한다.
    with path.open("rb") as data_file:  # Byte 단위 위치 이동을 위해 Read Binary 모드로 파일을 연다.
        data_file.seek(0, os.SEEK_END)  # 읽기 위치를 파일의 맨 끝으로 옮긴다.
        position = data_file.tell()  # 파일 끝의 Byte 위치를 저장한다.
        remaining = b""  # 블록 경계에서 잘린 한 줄의 일부를 보관한다.
        while position > 0:  # 파일의 맨 앞에 도달할 때까지 반복한다.
            read_size = min(block_size, position)  # 남은 크기를 넘지 않는 범위에서 읽을 크기를 정한다.
            position -= read_size  # 읽기 시작 위치를 앞쪽으로 이동한다.
            data_file.seek(position)  # 계산한 위치로 파일 읽기 지점을 이동한다.
            block = data_file.read(read_size) + remaining  # 새 블록과 이전에 잘린 줄을 이어 붙인다.
            lines = block.split(b"\n")  # 줄바꿈 Byte를 기준으로 여러 줄을 나눈다.
            remaining = lines[0]  # 앞 블록과 이어질 수 있는 첫 조각을 다음 반복까지 보관한다.
            for raw_line in reversed(lines[1:]):  # 완성된 줄을 파일 마지막 줄부터 거꾸로 꺼낸다.
                if raw_line.strip():  # 현재 줄이 빈 줄이 아닌지 확인한다.
                    yield raw_line.decode("utf-8")  # 현재 한 줄을 UTF-8 문자열로 바꿔 전달한다.
        if remaining.strip():  # 파일 맨 앞의 마지막 조각이 남았는지 확인한다.
            yield remaining.decode("utf-8")  # 맨 앞의 남은 줄도 UTF-8 문자열로 전달한다.
