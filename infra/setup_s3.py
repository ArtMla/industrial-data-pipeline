"""Create and configure S3 buckets for the predictive maintenance platform."""
import os
import boto3
from botocore.exceptions import ClientError

RAW_BUCKET = os.getenv("AWS_S3_RAW_BUCKET", "pred-maint-raw")
PROCESSED_BUCKET = os.getenv("AWS_S3_PROCESSED_BUCKET", "pred-maint-processed")
REGION = os.getenv("AWS_REGION", "eu-central-1")


def create_bucket(s3, bucket: str, region: str) -> None:
    try:
        if region == "us-east-1":
            s3.create_bucket(Bucket=bucket)
        else:
            s3.create_bucket(
                Bucket=bucket,
                CreateBucketConfiguration={"LocationConstraint": region},
            )
        print(f"Created:        s3://{bucket}/")
    except ClientError as e:
        if e.response["Error"]["Code"] in ("BucketAlreadyOwnedByYou", "BucketAlreadyExists"):
            print(f"Already exists: s3://{bucket}/")
        else:
            raise


def enable_versioning(s3, bucket: str) -> None:
    s3.put_bucket_versioning(
        Bucket=bucket,
        VersioningConfiguration={"Status": "Enabled"},
    )


def set_lifecycle_rule(s3, bucket: str) -> None:
    """Expire model artifacts older than 90 days to control storage costs."""
    s3.put_bucket_lifecycle_configuration(
        Bucket=bucket,
        LifecycleConfiguration={
            "Rules": [
                {
                    "ID": "expire-old-models",
                    "Status": "Enabled",
                    "Filter": {"Prefix": "models/"},
                    "Expiration": {"Days": 90},
                }
            ]
        },
    )
    print(f"Lifecycle rule: {bucket}/models/ → expire after 90 days")


def main() -> None:
    s3 = boto3.client("s3", region_name=REGION)

    for bucket in [RAW_BUCKET, PROCESSED_BUCKET]:
        create_bucket(s3, bucket, REGION)
        enable_versioning(s3, bucket)

    set_lifecycle_rule(s3, PROCESSED_BUCKET)

    print("\nS3 setup complete.")
    print(f"  Raw bucket:       s3://{RAW_BUCKET}/")
    print(f"  Processed bucket: s3://{PROCESSED_BUCKET}/")
    print("\nNext: python etl/upload_raw.py")


if __name__ == "__main__":
    main()
