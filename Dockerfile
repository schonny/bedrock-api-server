FROM python:3.12

COPY ./src /app

RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get install -y screen
RUN python -m pip install --upgrade pip
RUN python -m pip install flask requests
RUN mkdir -p /entrypoint/downloaded_server /entrypoint/logs /entrypoint/server /entrypoint/backups/incremental

WORKDIR /app
CMD ["python", "app.py"]
EXPOSE 8177
