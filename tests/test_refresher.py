from __future__ import annotations

from datetime import datetime, timezone
import ssl

from swclass_app import refresher


class FakeResponse:
    def __init__(self, body: bytes):
        self.body = body
        self.offset = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self, size: int = -1) -> bytes:
        if size == -1:
            size = len(self.body) - self.offset
        chunk = self.body[self.offset : self.offset + size]
        self.offset += len(chunk)
        return chunk


def test_download_archive_uses_browser_user_agent_and_unverified_tls_context(tmp_path, monkeypatch):
    calls = {}

    def fake_urlopen(request, timeout, context):
        calls["request"] = request
        calls["timeout"] = timeout
        calls["context"] = context
        return FakeResponse(b"Rar!\x1a\x07\x01\x00")

    monkeypatch.setattr(refresher.urllib.request, "urlopen", fake_urlopen)
    archive_path = tmp_path / "SwClass.rar"

    refresher.download_archive("https://example.test/SwClass.rar", archive_path)

    assert archive_path.read_bytes() == b"Rar!\x1a\x07\x01\x00"
    assert calls["request"].headers["User-agent"] == "Mozilla/5.0"
    assert calls["timeout"] == 60
    assert isinstance(calls["context"], ssl.SSLContext)
    assert calls["context"].check_hostname is False
    assert calls["context"].verify_mode == ssl.CERT_NONE


class FakeArchiveEntry:
    def __init__(self, filename, is_dir=False, is_file=True, body=b""):
        self.filename = filename
        self._is_dir = is_dir
        self._is_file = is_file
        self.body = body

    def isdir(self):
        return self._is_dir

    def is_file(self):
        return self._is_file


class FakeArchive:
    def __init__(self, entries):
        self.entries = entries

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def infolist(self):
        return self.entries

    def open(self, entry):
        return FakeResponse(entry.body)


def test_extract_archive_uses_python_rarfile_reader(tmp_path, monkeypatch):
    archive_path = tmp_path / "SwClass.rar"
    archive_path.write_bytes(b"fake-rar")
    extract_dir = tmp_path / "SwClass"
    entries = [
        FakeArchiveEntry("nested/", is_dir=True, is_file=False),
        FakeArchiveEntry("nested/file.txt", body=b"hello world"),
        FakeArchiveEntry(refresher.SOURCE_XLSX_NAME, body=b"xlsx"),
    ]
    calls = {}

    def fake_rar_file(path):
        calls["path"] = path
        return FakeArchive(entries)

    monkeypatch.setattr(refresher.rarfile, "RarFile", fake_rar_file)

    refresher.extract_archive(archive_path, extract_dir)

    assert calls["path"] == archive_path
    assert (extract_dir / "nested").is_dir()
    assert (extract_dir / "nested" / "file.txt").read_bytes() == b"hello world"


def test_extract_archive_fails_when_target_xlsx_is_missing(tmp_path, monkeypatch):
    archive_path = tmp_path / "SwClass.rar"
    archive_path.write_bytes(b"fake-rar")
    extract_dir = tmp_path / "SwClass"

    def fake_rar_file(path):
        return FakeArchive([FakeArchiveEntry("other.txt", body=b"other")])

    monkeypatch.setattr(refresher.rarfile, "RarFile", fake_rar_file)

    try:
        refresher.extract_archive(archive_path, extract_dir)
    except RuntimeError as exc:
        assert "未找到目标文件" in str(exc)
    else:
        raise AssertionError("extract_archive should fail when target xlsx is missing")


def test_extract_archive_extracts_real_swclass_rar(tmp_path):
    archive_path = refresher.Path(__file__).resolve().parent.parent / "SwClass.rar"
    extract_dir = tmp_path / "SwClass"

    refresher.extract_archive(archive_path, extract_dir)

    assert (extract_dir / refresher.SOURCE_XLSX_NAME).is_file()


def test_refresh_writes_xlsx_hashes_and_update_time(tmp_path, monkeypatch):
    archive_path = tmp_path / "SwClass.rar"
    extract_dir = tmp_path / "SwClass"
    output_json = tmp_path / "swclass.json"
    metadata_path = tmp_path / "refresh_state.json"

    def fake_download(source_url, path):
        path.write_bytes(b"archive")

    def fake_extract(path, directory):
        directory.mkdir(parents=True)
        (directory / refresher.SOURCE_XLSX_NAME).write_bytes(b"xlsx-v1")

    monkeypatch.setattr(refresher, "download_archive", fake_download)
    monkeypatch.setattr(refresher, "extract_archive", fake_extract)
    monkeypatch.setattr(refresher, "parse_industry_stocks", lambda path: [{"大众出版": ["600373.SH"]}])

    refresher.refresh(
        source_url="https://example.test/SwClass.rar",
        archive_path=archive_path,
        extract_dir=extract_dir,
        output_json=output_json,
        metadata_path=metadata_path,
        now=lambda: datetime(2026, 7, 6, 1, 2, 3, tzinfo=timezone.utc),
    )

    metadata = refresher.load_refresh_metadata(metadata_path)
    assert metadata["last_checked_at"] == "2026-07-06T01:02:03Z"
    assert metadata["last_updated_at"] == "2026-07-06T01:02:03Z"
    assert metadata["xlsx_size_bytes"] == 7
    assert metadata["xlsx_md5"] == "72e360cf18bb1ac94b2b1c485ccf4951"
    assert metadata["xlsx_sha256"] == "296ca376ec9dd5d8f3a6ce3a992739d7d10a45c73826d4181cf0db4937240382"


def test_refresh_preserves_update_time_when_xlsx_hash_is_unchanged(tmp_path, monkeypatch):
    archive_path = tmp_path / "SwClass.rar"
    extract_dir = tmp_path / "SwClass"
    output_json = tmp_path / "swclass.json"
    metadata_path = tmp_path / "refresh_state.json"

    def fake_download(source_url, path):
        path.write_bytes(b"archive")

    def fake_extract(path, directory):
        directory.mkdir(parents=True, exist_ok=True)
        (directory / refresher.SOURCE_XLSX_NAME).write_bytes(b"xlsx-v1")

    monkeypatch.setattr(refresher, "download_archive", fake_download)
    monkeypatch.setattr(refresher, "extract_archive", fake_extract)
    monkeypatch.setattr(refresher, "parse_industry_stocks", lambda path: [{"大众出版": ["600373.SH"]}])

    refresher.refresh(
        archive_path=archive_path,
        extract_dir=extract_dir,
        output_json=output_json,
        metadata_path=metadata_path,
        now=lambda: datetime(2026, 7, 6, 1, 2, 3, tzinfo=timezone.utc),
    )
    refresher.refresh(
        archive_path=archive_path,
        extract_dir=extract_dir,
        output_json=output_json,
        metadata_path=metadata_path,
        now=lambda: datetime(2026, 7, 7, 4, 5, 6, tzinfo=timezone.utc),
    )

    metadata = refresher.load_refresh_metadata(metadata_path)
    assert metadata["last_checked_at"] == "2026-07-07T04:05:06Z"
    assert metadata["last_updated_at"] == "2026-07-06T01:02:03Z"
