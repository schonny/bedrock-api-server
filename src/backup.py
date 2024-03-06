# backup.py
# err:2xxx

import gzip
import hashlib
import logging
import os
import shutil
import time

import helpers
import server
import settings
import world

def create(server_name=None, level_name=None, backup_name=None, overwrite=False, description=None, compress=False):  #201x
    if helpers.is_empty(server_name):
        return 'server-name is required', 2011

    server_path = os.path.join(settings.SERVER_PATH, server_name)
    if not os.path.exists(server_path):
        return f"server with this name '{server_name}' does not exists", 2012
    
    result = world.is_running(server_name, level_name)
    if result[1] > 0:
        return 'error by running-check', 2013, result
    elif result[0]['state']:
        return 'world is in use', 2014
    level_name = result[0]['level-name']

    current_time = time.time()
    if helpers.is_empty(backup_name):
        backup_name = time.strftime('%Y%m%d_%H%M%S', time.localtime(current_time)) + '_' + server_name + '_' + level_name
    else:
        backup_name = backup_name[:-len('.properties')] if backup_name.endswith('.properties') else backup_name

    backup_file = os.path.join(settings.BACKUPS_PATH, backup_name + '.properties')
    if os.path.exists(backup_file) and not helpers.is_true(overwrite):
        return 'backup with this name already exists', 2015, result

    backup_properties = {
        'server-name': server_name,
        'level-name': level_name,
        'backup-name': backup_name,
        'datetime': time.strftime('%Y-%m-%d %H:%M', time.localtime(current_time)),
        'description': description
    }
    result_properties = backup_properties.copy()
    result_properties['file-count'] = 0

    result = server.get_version(server_name)
    backup_properties['version'] = result[0]['version'] if result[1] == 0 else 'unknown'

    world_path = os.path.join(server_path, 'worlds', level_name)
    try:
        for root, _, files in os.walk(world_path):
            for file in files:
                input_file = os.path.join(root, file)
                relative_file_path = os.path.relpath(input_file, world_path)
                with open(input_file, 'rb') as f:
                    file_hash = hashlib.sha512(f.read()).hexdigest()
                backup_properties[file_hash] = relative_file_path
                result_properties['file-count'] += 1
                output_file = os.path.join(settings.INCREMENTAL_PATH, file_hash)
                if not os.path.exists(output_file):
                    if helpers.is_true(compress):
                        with open(input_file, 'rb') as f_in:
                            with gzip.open(output_file, 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)
                    else:
                        shutil.copy(input_file, output_file)
    except Exception as e:
        logging.error(f"unexpected error: {e}")
        return str(e), 2016

    # write backup
    result = helpers.write_properties(backup_file, backup_properties)
    if result[1] > 0:
        return 'error at write backup', 2018, result
    
    helpers.change_permissions_recursive(settings.BACKUPS_PATH, 0o777)
    return result_properties, 0

def restore(backup_name=None, server_name=None, level_name=None):  # 202x
    if helpers.is_empty(backup_name):
        return 'backup-name is required', 2021
    
    result = _get_backup_by_name(backup_name)
    if result[1] > 0:
        return 'backup does not exists', 2022, result
    
    result = helpers.read_properties(os.path.join(settings.BACKUPS_PATH, result[0]['backup-file']))
    if result[1] > 0:
        return 'cannot read backup-details', 2023
    properties = result[0]

    if helpers.is_empty(server_name):
        server_name = properties['server-name']
    
    server_path = os.path.join(settings.SERVER_PATH, server_name)
    if not os.path.exists(server_path):
        return f'server not exists: {server_name}', 2024

    if helpers.is_empty(level_name):
        level_name = properties['level-name']

    result = world.is_running(server_name, level_name)
    if result[1] == 0 and result[0]['state']:
        return 'world is in use', 2025

    # begin restoring
    for sha512 in properties.items():
        if len(sha512) == 128 and not os.path.exists(os.path.join(settings.INCREMENTAL_PATH, sha512)):
            return 'backup is corrupt. you should delete it.', 2026

    world_path = os.path.join(server_path, 'worlds', level_name)
    if os.path.exists(world_path):
        # remove old existing world
        result = helpers.remove_dirtree(world_path)
        if result[1] > 0:
            return 'cannot remove world', 2027, result

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

                input_file = os.path.join(settings.INCREMENTAL_PATH, sha512)
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
        return str(e), 2028
    
    helpers.change_permissions_recursive(world_path, 0o777)
    return {
        'server-name': server_name,
        'backup-name': backup_name,
        'level-name': level_name,
        'state': 'restored'
    }, 0

def list():  #203x
    result_list = {}
    for backup_file in [file for file in os.listdir(settings.BACKUPS_PATH) if os.path.isfile(os.path.join(settings.BACKUPS_PATH, file))]:
        result = helpers.read_properties(os.path.join(settings.BACKUPS_PATH, backup_file))
        if result[1] > 0:
            return 'cannot read backup-details', 2031
        
        properties = {'file-count': 0}
        for key, value in result[0].items():
            if len(key) == 128:
                properties['file-count'] += 1
            elif key != 'file-count':
                properties[key] = value

        backup_file = backup_file[:-len('.properties')] if backup_file.endswith('.properties') else backup_file
        result_list[backup_file] = properties
    return result_list, 0
    
def remove(backup_name=None):  # 204x
    if helpers.is_empty(backup_name):
        return 'backup-name is required', 2041
    
    result = _get_backup_by_name(backup_name)
    if result[1] > 0:
        return 'backup does not exists', 2042, result

    # remove backup-file
    backup_file = os.path.join(settings.BACKUPS_PATH, result[0]['backup-file'])
    if not os.path.exists(backup_file):
        return f'backup does not exists {backup_name}', 2043
    os.remove(backup_file)
    
    # list all referenced sha512-files
    linked_files = []
    for backup_file in [file for file in os.listdir(settings.BACKUPS_PATH) if os.path.isfile(os.path.join(settings.BACKUPS_PATH, file))]:
        result = helpers.read_properties(os.path.join(settings.BACKUPS_PATH, backup_file))
        if result[1] > 0:
            return 'cannot read backup-details', 2044
        properties = result[0]
        for sha512 in properties:
            if len(sha512) == 128 and sha512 not in linked_files:
                linked_files.append(sha512)

    # remove all unreferenced sha512-files
    try:
        for sha512 in os.listdir(settings.INCREMENTAL_PATH):
            if sha512 not in linked_files:
                os.remove(os.path.join(settings.INCREMENTAL_PATH, sha512))
        return {
            'backup-name': result[0]['backup-name'],
            'backup-file': result[0]['backup-file'],
            'state': 'removed'
        }, 0
    except Exception as e:
        logging.error(f"unexpected error: {e}")
        return str(e), 2045

def all_server():  # 205x
    states = {
        'backed-up': [],
        'still-running': [],
        'failed': []
    }
    for sub_result in helpers.parallel(create, server.get_created()):
        server_name = sub_result['parameters']
        result = sub_result['result']
        if result[1] == 0:
            states['backed-up'].append(server_name)
        elif result[1] == 2014:
            states['still-running'].append(server_name)
        else:
            states['failed'].append(server_name)
    return states, 0

def _get_backup_by_name(backup_name):  # 207x
    backup_name = backup_name[:-len('.properties')] if backup_name.endswith('.properties') else backup_name
    backup_file = backup_name + '.properties'
    
    if os.path.exists(os.path.join(settings.BACKUPS_PATH, backup_file)):
        return {
            'backup-name': backup_name,
            'backup-file': backup_file
        }, 0

    result = list()
    if result[1] > 0:
        return 'cannot find backup', 2071, result

    for file, properties in result[0].items():
        if file == backup_name or file == backup_file or properties['backup-name'] == backup_name or properties['backup-name'] == backup_file:
            return {
                'backup-name': properties['backup-name'],
                'backup-file': file
            }, 0

    return 'cannot found backup', 2072
