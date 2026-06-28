"""Upload the AI4I 2020 raw CSV to the S3 raw data lake."""
import hashlib
import os
from pathlib import Path

import boto3

RAW_BUCKET = os.getenv("AWS_S3_RAW_BUCKET", "pred-maint-raw")
REGION = os.getenv("AWS_REGION", "eu-central-1")
LOCAL_PATH = Path("data/raw/ai4i2020.csv")
S3_KEY = "ai4i/raw/ai4i2020.csv"


def md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    if not LOCAL_PATH.exists():
        print(f"ERROR: {LOCAL_PATH} not found.")
        print()
        print("Download the dataset:")
        print("  https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset")
        print()
        print("Save the CSV as:  data/raw/ai4i2020.csv")
        return

    checksum = md5(LOCAL_PATH)
    size_kb = LOCAL_PATH.stat().st_size / 1024
    print(f"File:    {LOCAL_PATH}  ({size_kb:.1f} KB,  md5={checksum[:8]}…)")

    s3 = boto3.client("s3", region_name=REGION)
    s3.upload_file(
        str(LOCAL_PATH),
        RAW_BUCKET,
        S3_KEY,
        ExtraArgs={"Metadata": {"md5": checksum}},
    )
    print(f"Uploaded → s3://{RAW_BUCKET}/{S3_KEY}")
    print("\nNext: make run-glue")


if __name__ == "__main__":
    main()
