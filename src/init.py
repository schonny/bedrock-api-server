# init.py

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

   