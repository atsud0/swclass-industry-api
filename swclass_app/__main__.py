from __future__ import annotations

import argparse

from .refresher import refresh
from .web import create_app, ensure_initial_data, start_daily_refresh


def main() -> None:
    parser = argparse.ArgumentParser(description="SwClass downloader and API")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("refresh", help="download, extract, and rebuild JSON")

    serve_parser = subparsers.add_parser("serve", help="start the Flask API")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", default=5000, type=int)
    serve_parser.add_argument(
        "--no-scheduler",
        action="store_true",
        help="disable the daily background refresh loop",
    )

    args = parser.parse_args()
    if args.command == "refresh":
        refresh()
        return

    if args.command == "serve":
        ensure_initial_data()
        if not args.no_scheduler:
            start_daily_refresh()
        app = create_app()
        app.run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
