"""Register the AWS Glue ETL job. Requires GLUE_ROLE_ARN env var — see infra/README.md."""
import os
import boto3

RAW_BUCKET = os.getenv("AWS_S3_RAW_BUCKET", "pred-maint-raw")
PROCESSED_BUCKET = os.getenv("AWS_S3_PROCESSED_BUCKET", "pred-maint-processed")
REGION = os.getenv("AWS_REGION", "eu-central-1")
GLUE_ROLE_ARN = os.getenv("GLUE_ROLE_ARN", "")
JOB_NAME = "pred-maint-etl"


def upload_script(s3, bucket: str) -> str:
    script_key = "glue-scripts/glue_job.py"
    with open("etl/glue_job.py", "rb") as f:
        s3.put_object(Bucket=bucket, Key=script_key, Body=f.read())
    path = f"s3://{bucket}/{script_key}"
    print(f"Script uploaded: {path}")
    return path


def register_job(glue, script_path: str) -> None:
    try:
        glue.delete_job(JobName=JOB_NAME)
        print(f"Deleted existing job: {JOB_NAME}")
    except glue.exceptions.EntityNotFoundException:
        pass

    glue.create_job(
        Name=JOB_NAME,
        Description="Validate AI4I CSV schema and convert to snappy Parquet",
        Role=GLUE_ROLE_ARN,
        Command={
            "Name": "glueetl",
            "ScriptLocation": script_path,
            "PythonVersion": "3",
        },
        DefaultArguments={
            "--TempDir": f"s3://{RAW_BUCKET}/glue-temp/",
            "--job-language": "python",
            "--RAW_BUCKET": RAW_BUCKET,
            "--PROCESSED_BUCKET": PROCESSED_BUCKET,
        },
        GlueVersion="4.0",
        NumberOfWorkers=2,
        WorkerType="G.1X",
        Timeout=10,
    )
    print(f"Glue job registered: {JOB_NAME}")


def main() -> None:
    if not GLUE_ROLE_ARN:
        print("ERROR: GLUE_ROLE_ARN is not set.")
        print("See infra/README.md → 'Create Glue IAM Role' for setup steps.")
        return

    s3 = boto3.client("s3", region_name=REGION)
    glue = boto3.client("glue", region_name=REGION)

    script_path = upload_script(s3, RAW_BUCKET)
    register_job(glue, script_path)

    print("\nGlue setup complete. Run the job:")
    print("  make run-glue")
    print("  # or: aws glue start-job-run --job-name pred-maint-etl")


if __name__ == "__main__":
    main()
