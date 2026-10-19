FROM python:3.12.12-slim-bookworm@sha256:593bd06efe90efa80dc4eee3948be7c0fde4134606dd40d8dd8dbcade98e669c
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY scripts/ scripts/
COPY config/ config/
COPY web/ web/
RUN mkdir data results && chown 10001:10001 results
USER 10001:10001
ENTRYPOINT ["python", "scripts/preview_start.py"]
