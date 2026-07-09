.PHONY: help setup upload-raw validate-schema run-glue load-features train api dashboard test lint build-all pause-rds pause-ecs

help:
	@echo ""
	@echo "  Industrial Predictive Maintenance Platform"
	@echo ""
	@echo "  Data pipeline:"
	@echo "    make upload-raw        Upload AI4I CSV to S3 raw bucket"
	@echo "    make validate-schema   Validate local CSV against pandera schema"
	@echo "    make run-glue          Trigger AWS Glue ETL job (CSV → Parquet)"
	@echo "    make load-features     Load Parquet features into PostgreSQL"
	@echo ""
	@echo "  ML:"
	@echo "    make train             Train XGBoost model + push artifact to S3"
	@echo ""
	@echo "  Local dev:"
	@echo "    make api               Start FastAPI dev server (port 8000)"
	@echo "    make dashboard         Start Next.js dev server (port 3000)"
	@echo ""
	@echo "  Quality:"
	@echo "    make test              Run pytest suite"
	@echo "    make lint              Run ruff linter"
	@echo ""
	@echo "  Docker:"
	@echo "    make build-all         Build api + dashboard Docker images"
	@echo "    make up                docker-compose up (all services)"
	@echo ""
	@echo "  AWS cost control:"
	@echo "    make pause-rds         Stop RDS instance"
	@echo "    make pause-ecs         Set ECS desired count to 0"
	@echo ""

setup:
	@cp -n .env.example .env || true
	@echo "Run: psql \$$DATABASE_URL -f infra/schema.sql"

upload-raw:
	python etl/upload_raw.py

validate-schema:
	python etl/validate_schema.py

run-glue:
	aws glue start-job-run --job-name pred-maint-etl

load-features:
	python etl/load_features.py

train:
	python ml/train.py

api:
	uvicorn api.main:app --reload --port 8000

dashboard:
	cd dashboard && npm run dev

test:
	pytest tests/ -v --tb=short

lint:
	ruff check . --select E,W,F

build-all:
	docker build -f api/Dockerfile . -t pred-maint-api:latest
	docker build dashboard/ -t pred-maint-dashboard:latest

up:
	docker-compose up

pause-rds:
	aws rds stop-db-instance --db-instance-identifier pred-maint-db
	@echo "RDS stopped. It will auto-start on next connection attempt."

pause-ecs:
	aws ecs update-service --cluster pred-maint-cluster --service pred-maint-api --desired-count 0
	aws ecs update-service --cluster pred-maint-cluster --service pred-maint-dashboard --desired-count 0
	@echo "ECS desired count set to 0. Tasks will stop within 30 seconds."
