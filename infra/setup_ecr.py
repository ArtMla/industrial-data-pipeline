"""Create ECR repositories for API and dashboard Docker images."""
import os
import boto3

REGION = os.getenv("AWS_REGION", "eu-central-1")
REPOS = ["pred-maint-api", "pred-maint-dashboard"]


def create_repo(ecr, name: str) -> str:
    try:
        resp = ecr.create_repository(
            repositoryName=name,
            imageScanningConfiguration={"scanOnPush": True},
            imageTagMutability="MUTABLE",
        )
        uri = resp["repository"]["repositoryUri"]
        print(f"Created:        {uri}")
    except ecr.exceptions.RepositoryAlreadyExistsException:
        resp = ecr.describe_repositories(repositoryNames=[name])
        uri = resp["repositories"][0]["repositoryUri"]
        print(f"Already exists: {uri}")
    return uri


def set_lifecycle(ecr, name: str) -> None:
    """Keep only the 10 most recent images to control storage costs."""
    ecr.put_lifecycle_policy(
        repositoryName=name,
        lifecyclePolicyText=(
            '{"rules":[{"rulePriority":1,"description":"Keep last 10",'
            '"selection":{"tagStatus":"any","countType":"imageCountMoreThan","countNumber":10},'
            '"action":{"type":"expire"}}]}'
        ),
    )


def main() -> None:
    ecr = boto3.client("ecr", region_name=REGION)
    uris = {}
    for repo in REPOS:
        uris[repo] = create_repo(ecr, repo)
        set_lifecycle(ecr, repo)

    registry = uris[REPOS[0]].split("/")[0]
    print(f"\nAdd to GitHub Actions secrets:")
    print(f"  ECR_REGISTRY={registry}")
    for repo, uri in uris.items():
        key = f"ECR_REPOSITORY_{repo.upper().replace('-', '_')}"
        print(f"  {key}={repo}")


if __name__ == "__main__":
    main()
