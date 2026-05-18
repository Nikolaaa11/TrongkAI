FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir uv && \
    uv pip install --system --no-cache .

COPY trongkai_engine ./trongkai_engine

EXPOSE 8000
CMD ["uvicorn", "trongkai_engine.main:app", "--host", "0.0.0.0", "--port", "8000"]
