FROM python:3.11-slim AS builder
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir --target=/app/requirements -r requirements.txt


FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /app/requirements /usr/local/lib/python3.11/site-packages/
COPY app.py app.py
EXPOSE 3000
RUN useradd -m appuser
USER appuser
CMD ["python3", "app.py"]