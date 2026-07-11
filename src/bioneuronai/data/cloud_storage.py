"""Optional cloud storage helpers for training artifacts.

The production code stays local-first. Cloud SDK imports are lazy so normal
CLI/API usage still works when Google Cloud packages or credentials are absent.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Iterable, Optional, Tuple, Union

PathLike = Union[str, Path]


def is_cloud_uri(value: Optional[PathLike]) -> bool:
    return isinstance(value, str) and value.startswith("gs://")


def _parse_gs_uri(uri: str) -> Tuple[str, str]:
    if not uri.startswith("gs://"):
        raise ValueError(f"Only gs:// URIs are supported: {uri}")
    bucket_and_name = uri[5:]
    bucket, _, name = bucket_and_name.partition("/")
    if not bucket:
        raise ValueError(f"Invalid GCS URI, missing bucket: {uri}")
    return bucket, name


def _storage_client():
    try:
        from google.cloud import storage  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on optional cloud SDK
        raise RuntimeError(
            "google-cloud-storage is required for gs:// artifact sync. "
            "Install locked dependencies or disable the gs:// path."
        ) from exc
    return storage.Client()


def _default_cache_dir() -> Path:
    return Path(os.getenv("BIONEURONAI_CLOUD_CACHE", "/tmp/bioneuronai_cloud"))


def _download_gcs_file(uri: str, local_path: Path) -> Path:
    bucket_name, object_name = _parse_gs_uri(uri)
    if not object_name:
        raise ValueError(f"GCS file URI must include an object name: {uri}")
    local_path.parent.mkdir(parents=True, exist_ok=True)
    bucket = _storage_client().bucket(bucket_name)
    bucket.blob(object_name).download_to_filename(str(local_path))
    return local_path


def _download_gcs_prefix(uri: str, local_dir: Path) -> Path:
    bucket_name, prefix = _parse_gs_uri(uri)
    if prefix and not prefix.endswith("/"):
        prefix = f"{prefix}/"
    local_dir.mkdir(parents=True, exist_ok=True)
    bucket = _storage_client().bucket(bucket_name)
    found = False
    for blob in bucket.list_blobs(prefix=prefix):
        if blob.name.endswith("/"):
            continue
        found = True
        relative = blob.name[len(prefix) :] if prefix else blob.name
        dest = local_dir / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        blob.download_to_filename(str(dest))
    if not found:
        raise FileNotFoundError(f"No objects found under GCS prefix: {uri}")
    return local_dir


def materialize_uri(value: PathLike, *, cache_dir: Path | None = None) -> Path:
    """Return a local path for a local path or gs:// URI.

    File URIs are downloaded to the cache. Prefix URIs ending in "/" are
    downloaded recursively and return a local directory.
    """
    if not is_cloud_uri(value):
        return Path(value)

    uri = str(value)
    cache_root = cache_dir or _default_cache_dir()
    bucket, object_name = _parse_gs_uri(uri)
    safe_bucket = bucket.replace("/", "_")
    if uri.endswith("/") or not Path(object_name).suffix:
        local_dir = cache_root / safe_bucket / object_name.strip("/").replace("/", "_")
        return _download_gcs_prefix(uri, local_dir)

    local_path = cache_root / safe_bucket / object_name
    return _download_gcs_file(uri, local_path)


def _iter_files(path: Path) -> Iterable[Path]:
    if path.is_file():
        yield path
        return
    for file_path in path.rglob("*"):
        if file_path.is_file():
            yield file_path


def upload_path(local_path: PathLike, destination_uri: str) -> None:
    """Upload a file or directory to a gs:// destination."""
    source = Path(local_path)
    if not source.exists():
        raise FileNotFoundError(f"Cannot upload missing path: {source}")
    if not destination_uri.startswith("gs://"):
        destination = Path(destination_uri)
        if source.is_dir():
            if destination.exists():
                shutil.rmtree(destination)
            shutil.copytree(source, destination)
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        return

    bucket_name, object_prefix = _parse_gs_uri(destination_uri)
    object_prefix = object_prefix.strip("/")
    bucket = _storage_client().bucket(bucket_name)

    for file_path in _iter_files(source):
        relative = file_path.name if source.is_file() else str(file_path.relative_to(source))
        blob_name = f"{object_prefix}/{relative}" if object_prefix else relative
        bucket.blob(blob_name.replace("\\", "/")).upload_from_filename(str(file_path))
