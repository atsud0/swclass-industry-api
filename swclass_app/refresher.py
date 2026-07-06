from __future__ import annotations

import shutil
import ssl
import urllib.request
from pathlib import Path

import rarfile

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
    extracted_files = 0
    with rarfile.RarFile(archive_path) as archive:
        for entry in archive.infolist():
            target_path = _safe_extract_path(base_dir, entry.filename)
            if entry.isdir():
                target_path.mkdir(parents=True, exist_ok=True)
                continue
            if not entry.is_file():
                continue
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(entry) as source, target_path.open("wb") as output:
                shutil.copyfileobj(source, output)
            extracted_files += 1

    expected_file = extract_dir / SOURCE_XLSX_NAME
    if extracted_files == 0 or not expected_file.is_file():
        raise RuntimeError(f"RAR 解压失败，未找到目标文件: {expected_file}")


def _safe_extract_path(base_dir: Path, archive_member: str) -> Path:
    target_path = (base_dir / archive_member).resolve()
    if target_path != base_dir and base_dir not in target_path.parents:
        raise ValueError(f"压缩包包含不安全路径: {archive_member}")
    return target_path
