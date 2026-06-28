FROM python:3.11-slim

WORKDIR /app

COPY api/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application and shared ML feature code
COPY api/ ./api/
COPY ml/__init__.py ./ml/__init__.py
COPY ml/features.py ./ml/features.py

# Non-root user for container security
RUN adduser --disabled-password --gecos "" --uid 1000 appuser
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
