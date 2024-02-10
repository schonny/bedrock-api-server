# init.py

import os
import server
import settings

# create Download-Path
if not os.path.exists(settings.DOWNLOADED_PATH):
    os.mkdir(settings.DOWNLOADED_PATH)
    os.chmod(settings.DOWNLOADED_PATH, 0o777)

# create server-path
if not os.path.exists(settings.SERVER_PATH):
    os.mkdir(settings.SERVER_PATH)
    os.chmod(settings.SERVER_PATH, 0o777)

# create logs-path
if not os.path.exists(settings.LOGS_PATH):
    os.mkdir(settings.LOGS_PATH)
    os.chmod(settings.LOGS_PATH, 0o777)

# init first world
first_server_name = os.environ.get('FIRST_SERVER_NAME')
first_server_port = os.environ.get('FIRST_SERVER_PORT')
if first_server_name is not None:
    if first_server_port is None:
        first_server_port = 19132
    