# settings.py

import os

DOWNLOADED_PATH = '/entrypoint/downloaded_server'
SERVER_PATH = '/entrypoint/server'
LOGS_PATH = '/entrypoint/logs'
BACKUPS_PATH = '/entrypoint/backups'
INCREMENTAL_PATH = os.path.join(BACKUPS_PATH, "incremental")

JOBBER_SOCKET_PATH = '/var/jobber/0'
JOBBER_CONFIG_FILE = '/app/jobber.yml'
