#!/bin/bash

mkdir -p /entrypoint/logs /var/jobber/0

echo python /app/cli_v1.py start-all-server
python /app/cli_v1.py start-all-server

echo python /app/cli_v1.py start-jobber
python /app/cli_v1.py start-jobber

echo python /app/app.py
python /app/app.py
