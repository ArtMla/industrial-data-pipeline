import os
import logging
import hashlib
from pathlib import Path

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

LOCAL_PATH = Path(__file__).parent.parent / "data" / "raw" / "ai4i2020.csv"
S3_KEY = "raw/ai4i2020.csv"


def _md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def upload(local_path: Path, bucket: str, key: str, region: str) -> None:
    if not local_path.exists():
        raise FileNotFoundError(f"Source file not found: {local_path}")

    s3 = boto3.client("s3", region_name=region)

    # Check if an identical object already exists
    try:
        head = s3.head_object(Bucket=bucket, Key=key)
        remote_etag = head["ETag"].strip('"')
        local_md5 = _md5(local_path)
        if remote_etag == local_md5:
            log.info("Remote object is identical — skipping upload.")
            return
    except ClientError as e:
        if e.response["Error"]["Code"] != "404":
            raise

    size_mb = local_path.stat().st_size / (1024 ** 2)
    log.info("Uploading %s (%.2f MB) → s3://%s/%s", local_path.name, size_mb, bucket, key)

    s3.upload_file(
        str(local_path),
        bucket,
        key,
        ExtraArgs={"ServerSideEncryption": "AES256"},
    )
    log.info("Upload complete.")


def main() -> None:
    bucket = os.environ.get("S3_BUCKET_NAME")
    region = os.environ.get("AWS_REGION", "eu-central-1")

    if not bucket:
        raise EnvironmentError("S3_BUCKET_NAME is not set.")

    try:
        upload(LOCAL_PATH, bucket, S3_KEY, region)
    except (BotoCoreError, ClientError) as e:
        log.error("AWS error: %s", e)
        raise SystemExit(1)
    except FileNotFoundError as e:
        log.error("%s", e)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
