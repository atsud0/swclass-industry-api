from __future__ import annotations

import json
from datetime import datetime, time

from swclass_app.web import create_app, seconds_until_next_run


def test_api_requires_bearer_token(tmp_path):
    output_json = tmp_path / "swclass.json"
    output_json.write_text(json.dumps([{"大众出版": ["600373.SH"]}], ensure_ascii=False), encoding="utf-8")
    app = create_app(output_json=output_json, token="secret")
    client = app.test_client()

    response = client.get("/api/swclass")

    assert response.status_code == 401


def test_api_returns_generated_json_with_valid_token(tmp_path):
    output_json = tmp_path / "swclass.json"
    expected = [{"大众出版": ["600373.SH"]}]
    output_json.write_text(json.dumps(expected, ensure_ascii=False), encoding="utf-8")
    app = create_app(output_json=output_json, token="secret")
    client = app.test_client()

    response = client.get("/api/swclass", headers={"Authorization": "Bearer secret"})

    assert response.status_code == 200
    assert response.get_json() == expected


def test_health_returns_refresh_metadata(tmp_path):
    output_json = tmp_path / "swclass.json"
    metadata_path = tmp_path / "refresh_state.json"
    metadata_path.write_text(
        json.dumps(
            {
                "last_checked_at": "2026-07-07T04:05:06Z",
                "last_updated_at": "2026-07-06T01:02:03Z",
                "xlsx_md5": "md5",
                "xlsx_sha256": "sha256",
                "xlsx_size_bytes": 7,
            }
        ),
        encoding="utf-8",
    )
    app = create_app(output_json=output_json, metadata_path=metadata_path, token="secret")
    client = app.test_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {
        "status": "ok",
        "last_checked_at": "2026-07-07T04:05:06Z",
        "last_updated_at": "2026-07-06T01:02:03Z",
        "xlsx_md5": "md5",
        "xlsx_sha256": "sha256",
        "xlsx_size_bytes": 7,
    }


def test_seconds_until_next_run_uses_today_when_time_has_not_passed():
    now = datetime(2026, 7, 6, 6, 30, 0)

    assert seconds_until_next_run(now, time(7, 0)) == 30 * 60


def test_seconds_until_next_run_uses_tomorrow_when_time_has_passed():
    now = datetime(2026, 7, 6, 8, 15, 0)

    assert seconds_until_next_run(now, time(7, 0)) == 22 * 60 * 60 + 45 * 60
