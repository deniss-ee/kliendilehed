import io
import os
import uuid
from typing import Optional
from app.config import settings
import structlog

logger = structlog.get_logger()

class LocalStorageClient:
    """Storage client supporting local filesystem directory and MinIO S3."""

    def __init__(self):
        self.use_local = settings.USE_LOCAL_STORAGE
        self.local_dir = settings.LOCAL_STORAGE_DIR
        self._minio_client = None

        if self.use_local:
            os.makedirs(self.local_dir, exist_ok=True)
        else:
            try:
                from minio import Minio
                self._minio_client = Minio(
                    endpoint=settings.MINIO_ENDPOINT,
                    access_key=settings.MINIO_ACCESS_KEY,
                    secret_key=settings.MINIO_SECRET_KEY,
                    secure=settings.MINIO_SECURE,
                )
                self.bucket = settings.MINIO_BUCKET_NAME
                if not self._minio_client.bucket_exists(self.bucket):
                    self._minio_client.make_bucket(self.bucket)
            except Exception as e:
                logger.warning("minio_init_fallback_to_local_disk", error=str(e))
                self.use_local = True
                os.makedirs(self.local_dir, exist_ok=True)

    def upload_image(
        self,
        file_bytes: bytes,
        content_type: str = "image/jpeg",
        filename_prefix: str = "custom",
    ) -> str:
        """Uploads image bytes to local folder or MinIO and returns URL."""
        extension = "jpg" if "jpeg" in content_type else "png" if "png" in content_type else "webp"
        filename = f"{filename_prefix}_{uuid.uuid4().hex[:12]}.{extension}"

        if self.use_local or self._minio_client is None:
            file_path = os.path.join(self.local_dir, filename)
            with open(file_path, "wb") as f:
                f.write(file_bytes)
            return f"/static/uploads/{filename}"

        # MinIO path
        object_name = f"{filename_prefix}/{filename}"
        self._minio_client.put_object(
            bucket_name=self.bucket,
            object_name=object_name,
            data=io.BytesIO(file_bytes),
            length=len(file_bytes),
            content_type=content_type,
        )
        scheme = "https" if settings.MINIO_SECURE else "http"
        return f"{scheme}://{settings.MINIO_ENDPOINT}/{self.bucket}/{object_name}"

storage_client = LocalStorageClient()
