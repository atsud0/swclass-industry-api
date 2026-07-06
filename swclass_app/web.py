from __future__ import annotations

import json
import os
import threading
import time
from datetime import datetime, time as datetime_time, timedelta
from pathlib import Path

from flask import Flask, Response, jsonify, request

from .config import DEFAULT_TOKEN, OUTPUT_JSON
from .refresher import refresh


def create_app(output_json: Path = OUTPUT_JSON, token: str | None = None) -> Flask:
    app = Flask(__name__)
    api_token = token or os.environ.get("SWCLASS_API_TOKEN", DEFAULT_TOKEN)

    @app.get("/health")
    def health() -> tuple[dict[str, str], int]:
        return {"status": "ok"}, 200

    @app.get("/api/swclass")
    def swclass() -> Response | tuple[dict[str, str], int]:
        if request.headers.get("Authorization") != f"Bearer {api_token}":
            return {"error": "unauthorized"}, 401
        if not output_json.exists():
            return {"error": "data_not_ready"}, 503
        return Response(
            output_json.read_text(encoding="utf-8"),
            mimetype="application/json; charset=utf-8",
        )

    return app


DEFAULT_REFRESH_TIME = datetime_time(7, 0)


def start_daily_refresh(refresh_time: datetime_time = DEFAULT_REFRESH_TIME) -> threading.Thread:
    def run_loop() -> None:
        while True:
            time.sleep(seconds_until_next_run(datetime.now(), refresh_time))
            try:
                refresh()
            except Exception as exc:
                print(f"refresh failed: {exc}", flush=True)

    thread = threading.Thread(target=run_loop, daemon=True)
    thread.start()
    return thread


def seconds_until_next_run(now: datetime, refresh_time: datetime_time) -> float:
    next_run = datetime.combine(now.date(), refresh_time)
    if next_run <= now:
        next_run += timedelta(days=1)
    return (next_run - now).total_seconds()


def load_json(output_json: Path = OUTPUT_JSON) -> object:
    return json.loads(output_json.read_text(encoding="utf-8"))
