import base64
from dataclasses import dataclass
import hashlib
from pathlib import Path
import time
from typing import Protocol
from uuid import uuid4

from fastapi import UploadFile
import httpx

from app.config import settings
from app.middleware.error_handler import AppException

STUDY_MATERIAL_EXTENSIONS = {".pdf", ".ppt", ".pptx", ".docx", ".zip"}
VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov"}

# Magic byte signatures for file type verification (do not trust browser MIME alone)
MAGIC_SIGNATURES: dict[str, list[tuple[int, bytes]]] = {
    ".pdf": [(0, b"%PDF-")],
    ".zip": [(0, b"PK\x03\x04"), (0, b"PK\x05\x06"), (0, b"PK\x07\x08")],
    ".docx": [(0, b"PK\x03\x04")],
    ".pptx": [(0, b"PK\x03\x04")],
    ".ppt": [(0, b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1")],
    ".mp4": [(4, b"ftyp")],
    ".mov": [(4, b"ftyp")],
    ".webm": [(0, b"\x1a\x45\xdf\xa3")],
}


@dataclass
class StoredFile:
    stored_key: str
    original_name: str
    size_bytes: int
    mime_type: str | None


class StorageBackend(Protocol):
    """Abstraction for file storage (local disk in dev, Cloudinary in prod)."""

    def save_bytes(
        self,
        data: bytes,
        original_name: str,
        mime_type: str | None,
        subdir: str = "",
    ) -> StoredFile: ...

    def read_bytes(self, stored_key: str) -> bytes: ...

    def resolve_path(self, stored_key: str) -> Path: ...

    def delete(self, stored_key: str) -> None: ...


class LocalStorageBackend:
    """Local filesystem storage backend rooted at settings.UPLOAD_DIR."""

    def __init__(self, base_dir: Path | None = None) -> None:
        if base_dir is not None:
            self.base_dir = base_dir
        else:
            upload_path = Path(settings.UPLOAD_DIR)
            if not upload_path.is_absolute():
                backend_root = Path(__file__).resolve().parent.parent.parent
                upload_path = backend_root / upload_path
            self.base_dir = upload_path
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_bytes(
        self,
        data: bytes,
        original_name: str,
        mime_type: str | None,
        subdir: str = "",
    ) -> StoredFile:
        ext = Path(original_name).suffix.lower()
        sanitized_name = f"{uuid4().hex}{ext}"
        target_dir = self.base_dir / subdir if subdir else self.base_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / sanitized_name
        target_path.write_bytes(data)

        stored_key = f"{subdir}/{sanitized_name}" if subdir else sanitized_name
        return StoredFile(
            stored_key=stored_key,
            original_name=Path(original_name).name,
            size_bytes=len(data),
            mime_type=mime_type,
        )

    def read_bytes(self, stored_key: str) -> bytes:
        path = self.resolve_path(stored_key)
        if not path.exists() or not path.is_file():
            raise AppException(404, "File not found.", "FILE_NOT_FOUND")
        return path.read_bytes()

    def resolve_path(self, stored_key: str) -> Path:
        resolved = (self.base_dir / stored_key).resolve()
        base_resolved = self.base_dir.resolve()
        if not str(resolved).startswith(str(base_resolved)):
            raise AppException(400, "Invalid file path.", "INVALID_FILE_PATH")
        return resolved

    def delete(self, stored_key: str) -> None:
        path = self.resolve_path(stored_key)
        if path.exists() and path.is_file():
            path.unlink()


class CloudinaryStorageBackend:
    """Private Cloudinary storage backend using signed authenticated uploads and downloads."""

    def __init__(self) -> None:
        self.cloud_name = settings.CLOUDINARY_CLOUD_NAME
        self.api_key = settings.CLOUDINARY_API_KEY
        self.api_secret = settings.CLOUDINARY_API_SECRET
        self.root_folder = settings.CLOUDINARY_FOLDER.strip("/") or "lms_private"
        if not (self.cloud_name and self.api_key and self.api_secret):
            raise AppException(
                500,
                "Cloudinary credentials are not configured.",
                "STORAGE_MISCONFIGURED",
            )

    def _sign_params(self, params: dict[str, str | int]) -> str:
        to_sign = "&".join(f"{k}={params[k]}" for k in sorted(params) if params[k] != "")
        return hashlib.sha1(f"{to_sign}{self.api_secret}".encode("utf-8")).hexdigest()

    def save_bytes(
        self,
        data: bytes,
        original_name: str,
        mime_type: str | None,
        subdir: str = "",
    ) -> StoredFile:
        ext = Path(original_name).suffix.lower()
        public_id = f"{self.root_folder}/{subdir}/{uuid4().hex}" if subdir else f"{self.root_folder}/{uuid4().hex}"
        if ext:
            public_id = f"{public_id}{ext}"

        timestamp = int(time.time())
        sign_params: dict[str, str | int] = {
            "access_mode": "authenticated",
            "public_id": public_id,
            "timestamp": timestamp,
            "type": "authenticated",
        }
        signature = self._sign_params(sign_params)

        upload_url = f"https://api.cloudinary.com/v1_1/{self.cloud_name}/raw/upload"
        resp = httpx.post(
            upload_url,
            data={
                "api_key": self.api_key,
                "timestamp": str(timestamp),
                "public_id": public_id,
                "type": "authenticated",
                "access_mode": "authenticated",
                "signature": signature,
            },
            files={"file": (Path(original_name).name, data, mime_type or "application/octet-stream")},
            timeout=30.0,
        )
        if resp.status_code >= 400:
            raise AppException(502, "Failed to upload file to cloud storage.", "CLOUD_UPLOAD_FAILED")

        return StoredFile(
            stored_key=public_id,
            original_name=Path(original_name).name,
            size_bytes=len(data),
            mime_type=mime_type,
        )

    def get_signed_download_url(self, stored_key: str, expires_in: int = 300) -> str:
        """Generate a short-lived signed Cloudinary download URL for authenticated raw assets."""
        expires_at = int(time.time()) + expires_in
        timestamp = int(time.time())
        sign_params: dict[str, str | int] = {
            "expires_at": expires_at,
            "public_id": stored_key,
            "timestamp": timestamp,
            "type": "authenticated",
        }
        signature = self._sign_params(sign_params)
        return (
            f"https://api.cloudinary.com/v1_1/{self.cloud_name}/raw/download"
            f"?api_key={self.api_key}&expires_at={expires_at}&public_id={stored_key}"
            f"&timestamp={timestamp}&type=authenticated&signature={signature}"
        )

    def read_bytes(self, stored_key: str) -> bytes:
        """Proxy private file bytes through the backend after RBAC/IDOR checks."""
        signed_url = self.get_signed_download_url(stored_key)
        resp = httpx.get(signed_url, timeout=30.0, follow_redirects=True)
        if resp.status_code == 404:
            raise AppException(404, "File not found in cloud storage.", "FILE_NOT_FOUND")
        if resp.status_code >= 400:
            raise AppException(502, "Failed to retrieve file from cloud storage.", "CLOUD_DOWNLOAD_FAILED")
        return resp.content

    def resolve_path(self, stored_key: str) -> Path:
        raise AppException(
            501,
            "Direct filesystem paths are not available when STORAGE_BACKEND=cloudinary.",
            "UNSUPPORTED_STORAGE_OPERATION",
        )

    def delete(self, stored_key: str) -> None:
        timestamp = int(time.time())
        sign_params: dict[str, str | int] = {
            "public_id": stored_key,
            "timestamp": timestamp,
            "type": "authenticated",
        }
        signature = self._sign_params(sign_params)
        destroy_url = f"https://api.cloudinary.com/v1_1/{self.cloud_name}/raw/destroy"
        httpx.post(
            destroy_url,
            data={
                "api_key": self.api_key,
                "public_id": stored_key,
                "timestamp": str(timestamp),
                "type": "authenticated",
                "signature": signature,
            },
            timeout=15.0,
        )


def get_storage_backend() -> StorageBackend:
    """Factory returning the configured storage backend (local or cloudinary)."""
    if settings.STORAGE_BACKEND.strip().lower() == "cloudinary":
        return CloudinaryStorageBackend()
    return LocalStorageBackend()


def _verify_magic_bytes(ext: str, data: bytes) -> bool:
    signatures = MAGIC_SIGNATURES.get(ext)
    if not signatures:
        return True
    return any(
        len(data) >= offset + len(sig) and data[offset : offset + len(sig)] == sig
        for offset, sig in signatures
    )


async def validate_and_save_upload(
    upload: UploadFile,
    *,
    allowed_extensions: set[str],
    subdir: str,
    storage: StorageBackend | None = None,
) -> StoredFile:
    """Validate extension, size limit, and magic bytes before saving via storage backend."""
    if not upload.filename:
        raise AppException(400, "Filename is required.", "INVALID_FILE")

    ext = Path(upload.filename).suffix.lower()
    if ext not in allowed_extensions:
        allowed_str = ", ".join(sorted(allowed_extensions))
        raise AppException(
            400,
            f"Unsupported file type '{ext}'. Allowed: {allowed_str}.",
            "INVALID_FILE_TYPE",
        )

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    data = await upload.read()
    if len(data) == 0:
        raise AppException(400, "Uploaded file is empty.", "EMPTY_FILE")
    if len(data) > max_bytes:
        raise AppException(
            413,
            f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB} MB.",
            "FILE_TOO_LARGE",
        )

    if not _verify_magic_bytes(ext, data):
        raise AppException(
            400,
            f"File content does not match '{ext}' signature.",
            "INVALID_FILE_SIGNATURE",
        )

    backend = storage or get_storage_backend()
    return backend.save_bytes(data, upload.filename, upload.content_type, subdir=subdir)
