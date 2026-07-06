from __future__ import annotations

import json

from openpyxl import Workbook

from swclass_app.parser import parse_industry_stocks, write_industry_json


def test_parse_industry_stocks_groups_codes_by_level3_industry(tmp_path):
    xlsx_path = tmp_path / "source.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["交易所", "股票代码", "公司简称", "新版三级行业"])
    sheet.append(["A股", "600373.SH", "中文传媒", "大众出版"])
    sheet.append(["A股", "601949.SH", "中国出版", "大众出版"])
    sheet.append(["A股", "600373.SH", "中文传媒", "大众出版"])
    sheet.append(["A股", "000001.SZ", "平安银行", "股份制银行"])
    sheet.append(["A股", None, "缺代码", "股份制银行"])
    workbook.save(xlsx_path)

    result = parse_industry_stocks(xlsx_path)

    assert result == [
        {"大众出版": ["600373.SH", "601949.SH"]},
        {"股份制银行": ["000001.SZ"]},
    ]


def test_write_industry_json_writes_utf8_json_atomically(tmp_path):
    output_path = tmp_path / "nested" / "swclass.json"
    data = [{"大众出版": ["600373.SH"]}]

    write_industry_json(data, output_path)

    assert json.loads(output_path.read_text(encoding="utf-8")) == data
