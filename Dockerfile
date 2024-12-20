FROM python:3-slim-bullseye

RUN echo "\n---------- update ----------" && \
    apt-get update && \
    apt-get upgrade -y && \
    \
    echo "\n---------- install ----------" && \
    apt-get install -y screen wget libcurl4 jq && \
    wget -O jobber.deb https://github.com/dshearer/jobber/releases/download/v1.4.4/jobber_1.4.4-1_amd64.deb && \
    dpkg -i jobber.deb && \
    pip install --upgrade pip && \
    pip install flask requests pyyaml && \
    \
    echo "\n---------- prepare ----------" && \
    mkdir -p /entrypoint/downloaded_server /entrypoint/logs /entrypoint/server /entrypoint/backups/incremental /var/jobber/0 && \
    \
    echo "\n---------- cleanup ----------" && \
    apt-get purge -y wget && \
    apt-get autoremove -y && \
    apt-get clean -y && \
    rm -rf /var/lib/apt/lists/* jobber.deb

COPY ./src /app
COPY run.sh /

WORKDIR /app
ENTRYPOINT ["bash", "/run.sh"]
EXPOSE 8177
