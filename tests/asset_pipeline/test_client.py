"""Offline tests for the shared asset_pipeline client (P-017).

No MinIO server required — get_client()'s env-var wiring is tested
directly, and every operation (ensure_bucket/upload_file/upload_bytes/
download_file/list_objects) is tested against a mock standing in for
minio.Minio, since the whole point of these functions is thin, mostly-
untestable-by-mocking-alone wiring around the SDK — what's worth locking
down is that they call the right SDK method with the right args and wrap
S3Error into AssetClientError consistently, not the SDK's own behavior.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

REPO = Path(__file__).resolve().parents[2]
PKG_DIR = REPO / "modules" / "asset-pipeline"

sys.path.insert(0, str(PKG_DIR))
from asset_pipeline import AssetClientError, client as ap_client  # noqa: E402


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for var in ("MINIO_ENDPOINT", "MINIO_ACCESS_KEY", "MINIO_SECRET_KEY", "MINIO_SECURE"):
        monkeypatch.delenv(var, raising=False)


def _s3_error():
    from minio.error import S3Error

    return S3Error(
        code="NoSuchBucket",
        message="test",
        resource="/x",
        request_id="r",
        host_id="h",
        response=MagicMock(),
    )


# ── get_client() env wiring ──────────────────────────────────────────────

def test_get_client_uses_defaults_with_no_env(monkeypatch):
    captured = {}

    def fake_minio(endpoint, access_key, secret_key, secure):
        captured.update(endpoint=endpoint, access_key=access_key, secret_key=secret_key, secure=secure)

    monkeypatch.setattr(ap_client, "Minio", fake_minio)
    ap_client.get_client()
    assert captured == {
        "endpoint": "localhost:9000",
        "access_key": "minioadmin",
        "secret_key": "minioadmin",
        "secure": False,
    }


def test_get_client_reads_env_vars(monkeypatch):
    monkeypatch.setenv("MINIO_ENDPOINT", "minio:9000")
    monkeypatch.setenv("MINIO_ACCESS_KEY", "hcpadmin")
    monkeypatch.setenv("MINIO_SECRET_KEY", "s3cr3t")
    monkeypatch.setenv("MINIO_SECURE", "true")

    captured = {}
    monkeypatch.setattr(
        ap_client, "Minio",
        lambda endpoint, access_key, secret_key, secure: captured.update(
            endpoint=endpoint, access_key=access_key, secret_key=secret_key, secure=secure
        ),
    )
    ap_client.get_client()
    assert captured == {
        "endpoint": "minio:9000",
        "access_key": "hcpadmin",
        "secret_key": "s3cr3t",
        "secure": True,
    }


def test_get_client_strips_url_scheme_from_endpoint(monkeypatch):
    """Regression: every prior consumer had to strip http(s):// from
    MINIO_ENDPOINT itself before this was centralized — a Compose-style env
    var often includes the scheme, but the MinIO SDK rejects it."""
    monkeypatch.setenv("MINIO_ENDPOINT", "http://minio:9000")
    captured = {}
    monkeypatch.setattr(
        ap_client, "Minio",
        lambda endpoint, access_key, secret_key, secure: captured.update(endpoint=endpoint),
    )
    ap_client.get_client()
    assert captured["endpoint"] == "minio:9000"


def test_get_client_explicit_args_win_over_env(monkeypatch):
    monkeypatch.setenv("MINIO_ENDPOINT", "from-env:9000")
    captured = {}
    monkeypatch.setattr(
        ap_client, "Minio",
        lambda endpoint, access_key, secret_key, secure: captured.update(endpoint=endpoint),
    )
    ap_client.get_client(endpoint="explicit:9000")
    assert captured["endpoint"] == "explicit:9000"


# ── ensure_bucket ─────────────────────────────────────────────────────────

def test_ensure_bucket_creates_when_missing():
    mock = MagicMock()
    mock.bucket_exists.return_value = False
    ap_client.ensure_bucket(mock, "my-bucket")
    mock.make_bucket.assert_called_once_with("my-bucket")


def test_ensure_bucket_is_noop_when_present():
    mock = MagicMock()
    mock.bucket_exists.return_value = True
    ap_client.ensure_bucket(mock, "my-bucket")
    mock.make_bucket.assert_not_called()


def test_ensure_bucket_wraps_s3_error():
    mock = MagicMock()
    mock.bucket_exists.side_effect = _s3_error()
    with pytest.raises(AssetClientError):
        ap_client.ensure_bucket(mock, "my-bucket")


# ── upload_file / upload_bytes / download_file / list_objects ────────────

def test_upload_file_calls_fput_object(tmp_path):
    mock = MagicMock()
    f = tmp_path / "img.png"
    f.write_bytes(b"data")
    key = ap_client.upload_file(mock, "bucket", "img.png", f)
    mock.fput_object.assert_called_once_with("bucket", "img.png", str(f))
    assert key == "img.png"


def test_upload_file_wraps_s3_error(tmp_path):
    mock = MagicMock()
    mock.fput_object.side_effect = _s3_error()
    f = tmp_path / "img.png"
    f.write_bytes(b"data")
    with pytest.raises(AssetClientError):
        ap_client.upload_file(mock, "bucket", "img.png", f)


def test_upload_bytes_calls_put_object_with_correct_length():
    mock = MagicMock()
    data = b"hello world"
    key = ap_client.upload_bytes(mock, "bucket", "k.txt", data, content_type="text/plain")
    assert key == "k.txt"
    _, kwargs = mock.put_object.call_args
    assert mock.put_object.call_args[0][0] == "bucket"
    assert mock.put_object.call_args[0][1] == "k.txt"
    assert kwargs["length"] == len(data)
    assert kwargs["content_type"] == "text/plain"


def test_download_file_calls_fget_object(tmp_path):
    mock = MagicMock()
    dest = tmp_path / "out.png"
    result = ap_client.download_file(mock, "bucket", "k.png", dest)
    mock.fget_object.assert_called_once_with("bucket", "k.png", str(dest))
    assert result == dest


def test_list_objects_returns_names():
    mock = MagicMock()
    obj_a = MagicMock(object_name="a.png")
    obj_b = MagicMock(object_name="b.png")
    mock.list_objects.return_value = [obj_a, obj_b]
    result = ap_client.list_objects(mock, "bucket", prefix="p/")
    assert result == ["a.png", "b.png"]
    mock.list_objects.assert_called_once_with("bucket", prefix="p/", recursive=True)


def test_list_objects_wraps_s3_error():
    mock = MagicMock()
    mock.list_objects.side_effect = _s3_error()
    with pytest.raises(AssetClientError):
        ap_client.list_objects(mock, "bucket")
