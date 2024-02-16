FROM python:3.12

COPY ./src /app

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y screen && \
    python -m pip install --upgrade pip && \
    python -m pip install flask requests && \
    mkdir -p /entrypoint/downloaded_server /entrypoint/logs /entrypoint/server /entrypoint/backups/incremental

WORKDIR /app
CMD ["python", "app.py"]
EXPOSE 8177
