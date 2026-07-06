from __future__ import annotations

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
ARCHIVE_PATH = DATA_DIR / "SwClass.rar"
EXTRACT_DIR = DATA_DIR / "SwClass"
OUTPUT_JSON = DATA_DIR / "swclass_industry_stocks.json"
SOURCE_URL = "https://www.swsresearch.com/swindex/pdf/SwClass2021/SwClass.rar"
SOURCE_XLSX_NAME = "最新个股申万行业分类(完整版-截至7月末).xlsx"
DEFAULT_TOKEN = "change-me"
