FROM python:3.12

COPY ./src /app

RUN apt-get update && \
    apt-get upgrade && \
	apt-get install -y screen && \
	pip install --upgrade pip && \
    pip install flask requests && \
    mkdir -p /entrypoint/downloaded_server /entrypoint/logs /entrypoint/server /entrypoint/backups/incremental

WORKDIR /app
CMD ["python", "app.py"]
EXPOSE 8177
