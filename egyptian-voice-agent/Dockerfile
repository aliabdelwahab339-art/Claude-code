FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential \
      ffmpeg \
      libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src ./src
COPY prompts ./prompts

RUN pip install --upgrade pip && pip install -e .

RUN mkdir -p /app/data /app/secrets

EXPOSE 8080

CMD ["python", "-m", "egyptian_voice_agent"]
