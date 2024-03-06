# app.py

#import init
from flask import Flask, Blueprint
import api_v1
import os
import settings

# create download-path
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

# create backups-path
if not os.path.exists(settings.BACKUPS_PATH):
    os.mkdir(settings.BACKUPS_PATH)
    os.chmod(settings.BACKUPS_PATH, 0o777)

# create backup-incremental-path
if not os.path.exists(settings.INCREMENTAL_PATH):
    os.mkdir(settings.INCREMENTAL_PATH)
    os.chmod(settings.INCREMENTAL_PATH, 0o777)

# create jobber-socket-path
if not os.path.exists(settings.JOBBER_SOCKET_PATH):
    os.mkdir(settings.JOBBER_SOCKET_PATH)
    os.chmod(settings.JOBBER_SOCKET_PATH, 0o777)

app = Flask(__name__)
app.register_blueprint(api_v1.api)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8177)
