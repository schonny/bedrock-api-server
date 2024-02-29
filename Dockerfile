FROM python:3-slim-bullseye

COPY ./src /app

RUN echo -e "\n---------- update ----------" && \
    apt-get update && \
    apt-get upgrade -y && \
    \
    echo -e "\n---------- install ----------" && \
    apt-get install -y screen wget libcurl4 && \
    wget -O jobber.deb https://github.com/dshearer/jobber/releases/download/v1.4.4/jobber_1.4.4-1_amd64.deb && \
    dpkg -i jobber.deb && \
    pip install --upgrade pip && \
    pip install flask requests && \
    \
    echo -e "\n---------- prepare ----------" && \
    mkdir -p /entrypoint/downloaded_server /entrypoint/logs /entrypoint/server /entrypoint/backups/incremental && \
    \
    echo -e "\n---------- cleanup ----------" && \
    apt-get purge -y wget && \
    apt-get autoremove -y && \
    apt-get clean -y && \
    rm -rf /var/lib/apt/lists/* jobber.deb

WORKDIR /app
CMD ["python", "app.py"]
EXPOSE 8177
