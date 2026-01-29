from typing import Optional

import oss2

from src.config import get_settings


class OSSService:
    def __init__(self) -> None:
        settings = get_settings().oss
        if not settings.access_key_id or not settings.access_key_secret:
            raise RuntimeError("OSS credentials missing: set OSS_ACCESS_KEY_ID and OSS_ACCESS_KEY_SECRET in .env")
        auth = oss2.Auth(settings.access_key_id, settings.access_key_secret)
        endpoint = settings.endpoint
        if not endpoint.startswith("http://") and not endpoint.startswith("https://"):
            endpoint = ("https://" if settings.use_https else "http://") + endpoint
        self.bucket = oss2.Bucket(auth, endpoint, settings.bucket)
        self.prefix = settings.prefix
        self.use_https = settings.use_https
        self.cname = settings.cname

    def _object_key_for_recording(self, recording_id: str) -> str:
        return f"{self.prefix}{recording_id}.wav"

    def object_key_for_recording(self, recording_id: str) -> str:
        return self._object_key_for_recording(recording_id)

    def object_key_for_recording_with_ext(self, recording_id: str, ext: str) -> str:
        ext_clean = (ext or "").strip().lstrip(".").lower() or "wav"
        return f"{self.prefix}{recording_id}.{ext_clean}"

    def sign_url_for_key(self, method: str, object_key: str, expire_seconds: int) -> str:
        return self.bucket.sign_url(method, object_key, expire_seconds)

    def generate_upload_url(self, recording_id: str, expire_seconds: int = 600) -> str:
        key = self._object_key_for_recording(recording_id)
        return self.bucket.sign_url("PUT", key, expire_seconds)

    def generate_download_url(self, recording_id: str, expire_seconds: int = 3600) -> str:
        key = self._object_key_for_recording(recording_id)
        return self.bucket.sign_url("GET", key, expire_seconds)

    def upload_local_file(self, object_key: str, local_path: str) -> None:
        self.bucket.put_object_from_file(object_key, local_path)

    def delete_object(self, recording_id: str) -> None:
        key = self._object_key_for_recording(recording_id)
        self.bucket.delete_object(key)

    def delete_object_key(self, object_key: str) -> None:
        self.bucket.delete_object(object_key)


_oss_service: Optional[OSSService] = None


def get_oss_service() -> OSSService:
    global _oss_service
    if _oss_service is None:
        _oss_service = OSSService()
    return _oss_service


