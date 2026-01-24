import os
from urllib.parse import urlparse

import boto3
from botocore.client import Config

from app.settings import settings


class StorageClient:
    def __init__(self):
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.MINIO_ENDPOINT,
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
            region_name="us-east-1",
            config=Config(signature_version="s3v4"),
        )

    def ensure_bucket(self, bucket: str):
        try:
            self.client.head_bucket(Bucket=bucket)
        except Exception:
            self.client.create_bucket(Bucket=bucket)

    def upload_file(self, local_path: str, bucket: str, key: str, content_type: str) -> int:
        self.ensure_bucket(bucket)
        self.client.upload_file(
            local_path,
            bucket,
            key,
            ExtraArgs={"ContentType": content_type},
        )
        return os.path.getsize(local_path)

    def presign_url(self, uri: str, expires_in: int = 900) -> str:
        parsed = urlparse(uri)
        if parsed.scheme != "s3":
            raise ValueError("unsupported uri")
        bucket = parsed.netloc
        key = parsed.path.lstrip("/")
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expires_in,
        )
