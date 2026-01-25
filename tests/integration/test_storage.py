import os
from pathlib import Path

import pytest

from app.services.storage import StorageClient


@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("MINIO_ENDPOINT"), reason="MINIO_ENDPOINT not set")
def test_minio_put_get(tmp_path):
    client = StorageClient()
    bucket = os.getenv("MINIO_BUCKET", "svf")
    local = tmp_path / "file.txt"
    local.write_text("hello", encoding="utf-8")

    key = "tests/file.txt"
    bytes_count = client.upload_file(str(local), bucket, key, "text/plain")
    assert bytes_count > 0

    dest = tmp_path / "download.txt"
    uri = f"s3://{bucket}/{key}"
    client.download_file(uri, str(dest))
    assert dest.read_text(encoding="utf-8") == "hello"


@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("MINIO_ENDPOINT"), reason="MINIO_ENDPOINT not set")
def test_minio_presign(tmp_path):
    client = StorageClient()
    bucket = os.getenv("MINIO_BUCKET", "svf")
    local = tmp_path / "file.txt"
    local.write_text("hello", encoding="utf-8")

    key = "tests/presign.txt"
    client.upload_file(str(local), bucket, key, "text/plain")
    uri = f"s3://{bucket}/{key}"
    url = client.presign_url(uri, expires_in=60)
    assert "X-Amz-Signature" in url
