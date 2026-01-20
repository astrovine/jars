FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/application

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --upgrade pip

RUN groupadd --gid 1000 jars \
    && useradd --uid 1000 --gid jars --shell /bin/bash --create-home jars

WORKDIR /application

COPY application/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

COPY application ./application


RUN chown -R jars:jars /application

USER jars

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "application.main:app", "--host", "0.0.0.0", "--port", "8000"]

