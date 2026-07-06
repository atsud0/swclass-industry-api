from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from openpyxl import load_workbook


STOCK_CODE_COLUMN = "股票代码"
LEVEL3_INDUSTRY_COLUMN = "新版三级行业"


def parse_industry_stocks(xlsx_path: Path) -> list[dict[str, list[str]]]:
    workbook = load_workbook(xlsx_path, read_only=True, data_only=True)
    try:
        sheet = workbook.active
        rows = sheet.iter_rows(values_only=True)
        headers = next(rows)
        stock_idx = _column_index(headers, STOCK_CODE_COLUMN)
        industry_idx = _column_index(headers, LEVEL3_INDUSTRY_COLUMN)

        grouped: dict[str, set[str]] = {}
        for row in rows:
            stock_code = _clean_cell(row[stock_idx] if stock_idx < len(row) else None)
            industry = _clean_cell(row[industry_idx] if industry_idx < len(row) else None)
            if not stock_code or not industry:
                continue
            grouped.setdefault(industry, set()).add(stock_code)

        return [{industry: sorted(codes)} for industry, codes in sorted(grouped.items())]
    finally:
        workbook.close()


def write_industry_json(data: list[dict[str, list[str]]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{output_path.name}.",
        suffix=".tmp",
        dir=output_path.parent,
        text=True,
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as temp_file:
            json.dump(data, temp_file, ensure_ascii=False, indent=2)
            temp_file.write("\n")
        os.replace(temp_name, output_path)
    except Exception:
        Path(temp_name).unlink(missing_ok=True)
        raise


def _column_index(headers: tuple[object, ...], column_name: str) -> int:
    normalized = [_clean_cell(value) for value in headers]
    try:
        return normalized.index(column_name)
    except ValueError as exc:
        raise ValueError(f"未找到必要列: {column_name}") from exc


def _clean_cell(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()
