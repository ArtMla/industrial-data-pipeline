"""
Set up RDS PostgreSQL (t3.micro) for the predictive maintenance platform.

RECOMMENDED: Use the AWS Console — faster and avoids IAM edge cases.

  Console steps:
    1. RDS → Create database → Standard create → PostgreSQL
    2. Template: Free tier
    3. DB identifier:     pred-maint-db
    4. Master username:   pred_maint
    5. Master password:   <your POSTGRES_PASSWORD>
    6. Instance class:    db.t3.micro
    7. Storage:           20 GB gp2
    8. Public access:     Yes (restrict via security group)
    9. New security group: allow port 5432 from your IP only
   10. Initial DB name:   pred_maint
   11. Create database (~5 min)

  After creation:
    export DATABASE_URL=postgresql://pred_maint:<pw>@<endpoint>:5432/pred_maint
    psql $DATABASE_URL -f infra/schema.sql

  COST NOTE:
    Stop the instance when not demoing:  make pause-rds
    (AWS auto-starts on next connection but auto-stops after 7 days of inactivity)

The boto3 equivalent is below for reference / CI automation.
"""
import os
import time
import boto3

REGION = os.getenv("AWS_REGION", "eu-central-1")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")


def create_instance(rds) -> None:
    rds.create_db_instance(
        DBInstanceIdentifier="pred-maint-db",
        DBInstanceClass="db.t3.micro",
        Engine="postgres",
        EngineVersion="16.3",
        MasterUsername="pred_maint",
        MasterUserPassword=DB_PASSWORD,
        DBName="pred_maint",
        AllocatedStorage=20,
        StorageType="gp2",
        PubliclyAccessible=True,
        MultiAZ=False,
        BackupRetentionPeriod=1,
        Tags=[{"Key": "Project", "Value": "pred-maint"}],
    )
    print("RDS create_db_instance submitted")


def wait_available(rds) -> str:
    print("Waiting for RDS to become available (5-10 min) …")
    while True:
        resp = rds.describe_db_instances(DBInstanceIdentifier="pred-maint-db")
        inst = resp["DBInstances"][0]
        status = inst["DBInstanceStatus"]
        print(f"  {status}")
        if status == "available":
            return inst["Endpoint"]["Address"]
        time.sleep(30)


def main() -> None:
    if not DB_PASSWORD:
        print("ERROR: POSTGRES_PASSWORD env var is not set.")
        return

    rds = boto3.client("rds", region_name=REGION)
    create_instance(rds)
    endpoint = wait_available(rds)

    url = f"postgresql://pred_maint:{DB_PASSWORD}@{endpoint}:5432/pred_maint"
    print(f"\nEndpoint: {endpoint}")
    print(f"DATABASE_URL={url}")
    print("\nNext: psql $DATABASE_URL -f infra/schema.sql")


if __name__ == "__main__":
    main()
