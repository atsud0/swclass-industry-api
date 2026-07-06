from __future__ import annotations

import hashlib
import json
import shutil
import ssl
import urllib.request
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

import rarfile

from .config import ARCHIVE_PATH, EXTRACT_DIR, OUTPUT_JSON, REFRESH_METADATA, SOURCE_URL, SOURCE_XLSX_NAME
from .parser import parse_industry_stocks, write_industry_json


def refresh(
    source_url: str = SOURCE_URL,
    archive_path: Path = ARCHIVE_PATH,
    extract_dir: Path = EXTRACT_DIR,
    output_json: Path = OUTPUT_JSON,
    metadata_path: Path = REFRESH_METADATA,
    now: Callable[[], datetime] | None = None,
) -> list[dict[str, list[str]]]:
    download_archive(source_url, archive_path)
    extract_archive(archive_path, extract_dir)
    xlsx_path = extract_dir / SOURCE_XLSX_NAME
    checked_at = _format_timestamp((now or _utc_now)())
    previous_metadata = load_refresh_metadata(metadata_path)
    xlsx_metadata = hash_file(xlsx_path)
    xlsx_changed = previous_metadata.get("xlsx_sha256") != xlsx_metadata["xlsx_sha256"]
    data = parse_industry_stocks(xlsx_path)
    write_industry_json(data, output_json)
    last_updated_at = previous_metadata.get("last_updated_at")
    if xlsx_changed or not last_updated_at:
        last_updated_at = checked_at
    write_refresh_metadata(
        {
            "last_checked_at": checked_at,
            "last_updated_at": last_updated_at,
            **xlsx_metadata,
        },
        metadata_path,
    )
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


def hash_file(path: Path) -> dict[str, str | int]:
    md5 = hashlib.md5(usedforsecurity=False)
    sha256 = hashlib.sha256()
    size_bytes = 0
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            size_bytes += len(chunk)
            md5.update(chunk)
            sha256.update(chunk)
    return {
        "xlsx_md5": md5.hexdigest(),
        "xlsx_sha256": sha256.hexdigest(),
        "xlsx_size_bytes": size_bytes,
    }


def load_refresh_metadata(metadata_path: Path = REFRESH_METADATA) -> dict[str, str | int | None]:
    if not metadata_path.exists():
        return {
            "last_checked_at": None,
            "last_updated_at": None,
            "xlsx_md5": None,
            "xlsx_sha256": None,
            "xlsx_size_bytes": None,
        }
    return json.loads(metadata_path.read_text(encoding="utf-8"))


def write_refresh_metadata(metadata: dict[str, str | int], metadata_path: Path = REFRESH_METADATA) -> None:
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = metadata_path.with_suffix(metadata_path.suffix + ".tmp")
    temporary_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(metadata_path)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _format_timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
