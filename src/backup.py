# backup.py

import gzip
import hashlib
import helpers
import logging
import os
import server
import settings
import shutil
import time

INCREMENTAL_PATH = os.path.join(settings.BACKUPS_PATH, "incremental")

# create backups-path
if not os.path.exists(INCREMENTAL_PATH):
    os.mkdir(INCREMENTAL_PATH)
    os.chmod(INCREMENTAL_PATH, 0o777)

def create(server_name, level_name=None, backup_name=None, description=None, compress=False):  #30xx
    if helpers.is_empty(server_name):
        return 'server-name is required', 3001
    
    if server.is_running(server_name):
        return 'this server is running', 3002
    
    result = server.get_world(server_name, level_name)
    if result[1] > 0:
        return 'cannot create backup', 3003, result
    level_name = result[0]

    result = server.get_server_version(server_name)
    if result[1] > 0:
        return 'cannot create backup', 3004, result
    server_version = result[0]

    current_time = time.time()
    if helpers.is_empty(backup_name):
        backup_name = time.strftime('%Y%m%d_%H%M%S', time.localtime(current_time))
    backup_file = os.path.join(settings.BACKUPS_PATH, backup_name)
    if os.path.exists(backup_file):
        return 'cannot create backup', 3004, result
    
    file_list = f"server-name={server_name}\nserver-version={server_version}\nlevel-name={level_name}\ndatetime={time.strftime('%Y-%m-%d %H:%M', time.localtime(current_time))}\n"
    if description:
        file_list += f"description={description}\n"

    world_path = os.path.join(settings.SERVER_PATH, server_name, 'worlds', level_name)
    try:
        for root, _, files in os.walk(world_path):
            for file in files:
                input_file = os.path.join(root, file)
                relative_file_path = os.path.relpath(input_file, world_path)
                with open(input_file, 'rb') as f:
                    file_hash = hashlib.sha512(f.read()).hexdigest()
                file_list += f"{file_hash}={relative_file_path}\n"
                output_file = os.path.join(INCREMENTAL_PATH, file_hash)
                if not os.path.exists(output_file):
                    if helpers.is_true(compress):
                        with open(input_file, 'rb') as f_in:
                            with gzip.open(output_file, 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)
                    else:
                        shutil.copy(input_file, output_file)
    except Exception as e:
        logging.error(f"unexpected error: {e}")
        return str(e), 3005

    with open(backup_file, 'w') as f:
        f.write(file_list)
    
    helpers.change_permissions_recursive(settings.BACKUPS_PATH, 0o777)
    return {'backup-name':backup_name},0

def restore(backup_name, server_name=None, level_name=None):  # 31xx
    if helpers.is_empty(backup_name):
        return 'backup-name is required', 3101
    
    result = helpers.read_properties(os.path.join(settings.BACKUPS_PATH, backup_name))
    if result[1] > 0:
        return 'cannot read backup-details', 3102
    properties = result[0]

    if helpers.is_empty(server_name):
        server_name = properties['server-name']
    
    server_path = os.path.join(settings.SERVER_PATH, server_name)
    if not os.path.exists(server_path):
        return 'server-name not exists', 3103
    
    if server.is_running(server_name):
        return 'this server is running', 3104

    if helpers.is_empty(level_name):
        level_name = properties['level-name']
    
    for sha512 in properties.items():
        if len(sha512) == 128 and not os.path.exists(os.path.join(INCREMENTAL_PATH, sha512)):
            return 'backup is corrupt. you should delete it.', 3105

    world_path = os.path.join(server_path, 'worlds', level_name)
    if os.path.exists(world_path):
        # remove old existing world
        result = helpers.remove_dirtree(world_path)
        if result[1] > 0:
            return 'cannot remove world', 3106, result

    def is_gzip_file(file_path):
        try:
            with gzip.open(file_path, 'rb') as f:
                f.read(1)
                return True
        except Exception as e:
            return False
    
    try:
        for sha512, file_name in properties.items():
            if len(sha512) == 128:
                output_file = os.path.join(world_path, file_name.strip())
                if not os.path.exists(os.path.dirname(output_file)):
                    os.makedirs(os.path.dirname(output_file))

                input_file = os.path.join(INCREMENTAL_PATH, sha512)
                if is_gzip_file(input_file):
                    with gzip.open(input_file, 'rb') as f_in:
                        with open(output_file, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                else:
                    shutil.copy(input_file, output_file)

                if file_name == 'levelname.txt':
                    with open(output_file, 'w') as level_file:
                        level_file.write(level_name)
    except Exception as e:
        logging.error(f"unexpected error: {e}")
        return str(e), 3107
    
    helpers.change_permissions_recursive(world_path, 0o777)
    return 'restored', 0

def list():  #32xx
    result_list = {}
    for backup_file in [file for file in os.listdir(settings.BACKUPS_PATH) if os.path.isfile(os.path.join(settings.BACKUPS_PATH, file))]:
        result = helpers.read_properties(os.path.join(settings.BACKUPS_PATH, backup_file))
        if result[1] > 0:
            return 'cannot read backup-details', 3201
        properties = result[0]
        result_list[backup_file] = {
            'backup-name': backup_file,
            'server-name': properties['server-name'],
            'server-version': properties['server-version'],
            'level-name': properties['level-name'],
            'datetime': properties['datetime'],
            'description': properties['description'] if 'description' in properties else None
        }
    return result_list, 0
    
def remove(backup_name):  # 33xx
    if helpers.is_empty(backup_name):
        return 'backup-name is required', 3301
    
    # remove backup-file
    backup_file = os.path.join(settings.BACKUPS_PATH, backup_name)
    if not os.path.exists(backup_file):
        return f'backup does not exists {backup_name}', 3303
    os.remove(backup_file)
    
    # list all referenced sha512-files
    linked_files = []
    for backup_file in [file for file in os.listdir(settings.BACKUPS_PATH) if os.path.isfile(os.path.join(settings.BACKUPS_PATH, file))]:
        result = helpers.read_properties(os.path.join(settings.BACKUPS_PATH, backup_file))
        if result[1] > 0:
            return 'cannot read backup-details', 3304
        properties = result[0]
        for sha512 in properties:
            if len(sha512) == 128 and sha512 not in linked_files:
                linked_files.append(sha512)

    # remove all unreferenced sha512-files
    try:
        for sha512 in os.listdir(INCREMENTAL_PATH):
            if sha512 not in linked_files:
                os.remove(os.path.join(INCREMENTAL_PATH, sha512))
        return 'removed', 0
    except Exception as e:
        logging.error(f"unexpected error: {e}")
        return str(e), 3305
