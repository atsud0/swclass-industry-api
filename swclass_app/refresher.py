from __future__ import annotations

import shutil
import ssl
import urllib.request
from pathlib import Path

import libarchive

from .config import ARCHIVE_PATH, EXTRACT_DIR, OUTPUT_JSON, SOURCE_URL, SOURCE_XLSX_NAME
from .parser import parse_industry_stocks, write_industry_json


def refresh(
    source_url: str = SOURCE_URL,
    archive_path: Path = ARCHIVE_PATH,
    extract_dir: Path = EXTRACT_DIR,
    output_json: Path = OUTPUT_JSON,
) -> list[dict[str, list[str]]]:
    download_archive(source_url, archive_path)
    extract_archive(archive_path, extract_dir)
    xlsx_path = extract_dir / SOURCE_XLSX_NAME
    data = parse_industry_stocks(xlsx_path)
    write_industry_json(data, output_json)
    return data


def download_archive(source_url: str, archive_path: Path) -> None:
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(
        source_url,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    context = ssl._create_unverified_context()
    with urllib.request.urlopen(request, timeout=60, context=context) as response:
        with archive_path.open("wb") as output:
            shutil.copyfileobj(response, output)


def extract_archive(archive_path: Path, extract_dir: Path) -> None:
    extract_dir.mkdir(parents=True, exist_ok=True)
    base_dir = extract_dir.resolve()
    with libarchive.file_reader(str(archive_path)) as entries:
        for entry in entries:
            target_path = _safe_extract_path(base_dir, entry.pathname)
            if entry.filetype == "directory":
                target_path.mkdir(parents=True, exist_ok=True)
                continue
            if entry.filetype != "file":
                continue
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with target_path.open("wb") as output:
                for block in entry.get_blocks():
                    output.write(block)


def _safe_extract_path(base_dir: Path, archive_member: str) -> Path:
    target_path = (base_dir / archive_member).resolve()
    if target_path != base_dir and base_dir not in target_path.parents:
        raise ValueError(f"压缩包包含不安全路径: {archive_member}")
    return target_path
