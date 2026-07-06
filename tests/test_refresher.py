from __future__ import annotations

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
    def __init__(self, pathname, filetype, blocks):
        self.pathname = pathname
        self.filetype = filetype
        self._blocks = blocks

    def get_blocks(self):
        return self._blocks


class FakeArchiveReader:
    def __init__(self, entries):
        self.entries = entries

    def __enter__(self):
        return self.entries

    def __exit__(self, exc_type, exc, traceback):
        return False


def test_extract_archive_uses_python_libarchive_reader(tmp_path, monkeypatch):
    archive_path = tmp_path / "SwClass.rar"
    archive_path.write_bytes(b"fake-rar")
    extract_dir = tmp_path / "SwClass"
    entries = [
        FakeArchiveEntry("nested/", "directory", []),
        FakeArchiveEntry("nested/file.txt", "file", [b"hello ", b"world"]),
    ]
    calls = {}

    def fake_file_reader(path):
        calls["path"] = path
        return FakeArchiveReader(entries)

    monkeypatch.setattr(refresher.libarchive, "file_reader", fake_file_reader)

    refresher.extract_archive(archive_path, extract_dir)

    assert calls["path"] == str(archive_path)
    assert (extract_dir / "nested").is_dir()
    assert (extract_dir / "nested" / "file.txt").read_bytes() == b"hello world"
