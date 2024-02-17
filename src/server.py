# server.py

from zipfile import ZipFile
from datetime import datetime

import helpers
import logging
import os
import re
import requests
import settings
import shutil
import subprocess
import time

def get_online_version(preview=None):  # 11xx
    headers = {'User-Agent': 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1)'}
    server_version_url = 'https://minecraft.net/de-de/download/server/bedrock/';

    try:
        response = requests.get(server_version_url, headers=headers)
        response.raise_for_status()

        if response.status_code == 200:
            zip_url = r'https://.+linux.+-([0-9\.]+).zip'
            if helpers._is_true(preview):
                zip_url = r'https://.+linux-preview.+-([0-9\.]+).zip'

            matches = re.search(zip_url, response.text)
            if matches and len(matches.groups()) == 1:
                return matches.group(1), 0
            else:
                logging.error('Error: result cannot be parsed')
                return 'result cannot be parsed', 1101
        else:
            logging.error('Error: cat not read from external server')
            return 'cannot read from external server', 1102
                
    except Exception as e:
        logging.error(f"Error: {e}")
        return str(e), 1103

def download(version=None):  # 12xx
    if helpers._is_empty(version):
        result = get_online_version()
        if result[1] == 0:
            version = result[0]
        else:
            return 'cannot get online-version', 1201, result

    zip_path = os.path.join(settings.DOWNLOADED_PATH, f'{version}.zip')
    if os.path.exists(zip_path):
        logging.debug(f"server already downloaded: {zip_path}")
        return f'server already downloaded: {version}', 0
    
    def _download(url, zip_path):
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()

            with open(zip_path, 'wb') as f:
                shutil.copyfileobj(response.raw, f)
            logging.debug(f"downloaded: {url}")
            return True
        except Exception as e:
            logging.error(f"cannot download: {e}")
            return str(e)

    if not os.path.exists(zip_path):
        url = f'https://minecraft.azureedge.net/bin-linux/bedrock-server-{version}.zip'
        result = _download(url, zip_path)
        if result != True:
            url = f'https://minecraft.azureedge.net/bin-linux-preview/bedrock-server-{version}.zip'
            if not _download(url, zip_path):
                if os.path.exists(zip_path):
                    os.remove(zip_path)
                    return result, 1202
        
        helpers.change_permissions_recursive(zip_path, 0o777)
    else:
        logging.debug(f"file already exists: {zip_path}")
        
    return f'server downloaded: {version}', 0

def get_downloaded_versions():  # 13xx
    try:
        files = os.listdir(settings.DOWNLOADED_PATH)
        versions = [os.path.splitext(file)[0] for file in files if file.endswith('.zip')]
        if len(versions) == 0:
            return 'none available', 1301
        versions = sorted(versions, key=lambda x: [int(part) for part in x.split('.')], reverse=True)
        return versions, 0
    except Exception as e:
        logging.error(f"cannot read filesystem: {e}")
        return str(e), 1302

def create(default_properties={}):  # 14xx
    if 'server-name' in default_properties:
        server_name = default_properties['server-name']
    else:
        return 'server-name is required', 1401
            
    if 'server-version' in default_properties:
        server_version = default_properties['server-version']
        del default_properties['server-version']
    else:
        result = get_downloaded_versions()
        if result[1] == 0:
            server_version = result[0][0]
        else:
            return 'a server must be downloaded first.', 1403, result

    # unzip to server-path
    zip_path = os.path.join(settings.DOWNLOADED_PATH, f'{server_version}.zip')
    server_path = os.path.join(settings.SERVER_PATH, server_name)
    if not os.path.exists(zip_path):
        return 'this server version does not exist.', 1404
    if not os.path.exists(server_path):
        with ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(server_path)
    else:
        logging.debug(f"server already exists: {server_path}")
        return f'server already exists: {server_name}', 1405
        
    # set version
    server_version_file = os.path.join(server_path, 'version')
    with open(server_version_file, 'w') as version_file:
        version_file.write(server_version)
    
    # write server_default.properties
    try:
        default_properties_file = os.path.join(server_path, 'server_default.properties')
        with open(default_properties_file, 'w') as file:
            for key, value in default_properties.items():
                file.write(f'{key}={value}\n')
        logging.debug('server_default.properties created')
    except Exception as e:
        logging.error(f"unexpected error: {e}")
        return str(e), 1406
    
    # backup from server.properties
    properties_file = os.path.join(server_path, 'server.properties')
    properties_copy = os.path.join(server_path, 'server_copy.properties')
    shutil.copy(properties_file, properties_copy)

    helpers.change_permissions_recursive(server_path, 0o777)
    return f'{server_name}', 0

def remove(server_name=None):  # 15xx
    if helpers._is_empty(server_name):
        return 'server-name is required', 1501
    
    if is_running(server_name):
        return 'this server is running', 1502
    
    server_path = os.path.join(settings.SERVER_PATH, server_name)
    result = helpers.remove_dirtree(server_path)
    if result[1] > 0:
        return 'cannot remove server', 1503, result

    try:
        os.remove(os.path.join(settings.LOGS_PATH, server_name))
    except Exception as e:
        logging.error(f"unexpected error: {e}")
        return str(e), 1504
    
    logging.debug(f'successfully removed {server_path}')
    return f'{server_name}', 0

def start(start_properties={}):  # 16xx
    if 'server-name' in start_properties:
        server_name = start_properties['server-name']
    else:
        return 'server-name is required', 1601

    server_path = os.path.join(settings.SERVER_PATH, server_name)
    if not os.path.exists(server_path):
        return f"server with this name '{server_name}' does not exists", 1602
        
    if is_running(server_name):
        return 'server already running', 0
    
    # read server_default.properties
    try:
        default_properties_file = os.path.join(server_path, 'server_default.properties')
        default_properties = helpers.read_properties(default_properties_file)[0]
    except Exception as e:
        logging.error(f"unexpected error: {e}")
        return str(e), 1603
    
    # merge properties (server > default > start)
    try:
        server_properties_file = os.path.join(server_path, 'server_copy.properties')
        server_properties = helpers.read_properties(server_properties_file)[0]
        # merge
        for key, value in server_properties.items():
            if key in start_properties:
                server_properties[key] = start_properties[key]
            elif key in default_properties:
                server_properties[key] = default_properties[key]
        server_properties['server-name'] = server_name

        # check server-port
        if not is_port_free(server_properties['server-port']):
            return f'server-port is already in use: {server_properties['server-port']}', 1604
    
        # write server.properties
        server_properties_file = os.path.join(server_path, 'server.properties')
        with open(server_properties_file, 'w') as file:
            for key, value in server_properties.items():
                file.write(f'{key}={value}\n')

        logging.debug('successfully merged properties')
    except Exception as e:
        logging.error(f"unexpected error: {e}")
        return str(e), 1605
    
    # start server in screen-session
    try:
        server_log = os.path.join(settings.LOGS_PATH, server_name)
        if os.path.exists(server_log):
            os.remove(server_log)
        subprocess.run([
            'screen',
            '-dmS', server_name,
            '-L', '-Logfile', server_log,
            'bash', '-c', f'cd {server_path} ; LD_LIBRARY_PATH=. ; ./bedrock_server'
        ])
    except Exception as e:
        logging.error(f"unexpected error: {e}")
        return str(e), 1607

    # wait for running
    for i in range(60):
        time.sleep(1)
        states = parse_log(server_name)
        if states['start_time'] and states['started_time'] and states['start_time'] < states['started_time']:
            logging.debug(f'successfully started {server_name}')
            return f'{server_name}', 0
        logging.debug(f'starting {server_name}')

    # abourt
    subprocess.run(["screen", "-S", server_name, "-X", "quit"])
    return f'cannot start server: {server_name}', 1608

def list():
    created_server = get_created()
    if len(created_server) == 0:
        return 'no server created', 0
    
    running_server = get_running()
    result_list = {
        "created-server": created_server,
        "running-server": running_server,
        "server-list": {}
    }
    
    for server_name in created_server:
        result = get_server_version(server_name)
        server_version = None if result[1] == 1 else result[0]

        properties_file = os.path.join(settings.SERVER_PATH, server_name, 'server.properties')
        result = helpers.read_properties(properties_file)
        properties = result[0] if result[1] == 0 else {}

        result = get_worlds(server_name)
        worlds = result[0] if result[1] == 0 else []

        if len(worlds) == 0:
            # this server has never been started. therefore the server.properties are still in their original state.
            default_properties_file = os.path.join(settings.SERVER_PATH, server_name, 'server_default.properties')
            result = helpers.read_properties(default_properties_file)
            default_properties = result[0] if result[1] == 0 else {}
            print(default_properties)
            for key in properties:
                if key in default_properties:
                    properties[key] = default_properties[key]
            properties['server-name'] = server_name

        result_list["server-list"][server_name] = {
            "server-name": server_name,
            "server-version": server_version,
            "is-running": server_name in running_server,
            "server-port": properties['server-port'] if 'server-port' in properties else None,
            "server-portv6": properties['server-portv6'] if 'server-portv6' in properties else None,
            "level-name": properties['level-name'] if 'level-name' in properties else None,
            "worlds": worlds
        }
    return result_list, 0

def stop(server_name, wait_for_disconnected_user=False):  # 17xx
    if helpers._is_empty(server_name):
        return 'server-name is required', 1701
        
    if not is_running(server_name):
        return 'server already stopped', 0

    sec = 5
    if wait_for_disconnected_user:
        say_stop = 0
        states = parse_log(server_name)
        while parse_log(server_name)['user_count'] > 0:
            if say_stop <= 0:
                say_stop = 60 // sec
                say_to_server(server_name, 'This server is supposed to be shut down. Please finish your game.')
            say_stop -= 1
            time.sleep(sec)

    elif parse_log(server_name)['user_count'] > 0:
        say_to_server(server_name, 'This server will shutdown in 1 minute. Please finish your game.')
        for i in range(60 // sec, 0, -1):
            if parse_log(server_name)['user_count'] <= 0:
                break
            if i * sec in [30, 20, 10]:
                say_to_server(server_name, f'This server will shutdown in {i * sec} seconds. Please finish your game.')
            time.sleep(sec)
            
    result = send_command(server_name, 'stop')
    if result[1] != 0:
        return 'cannot send stop-command', 1702, result

    for i in range(60):
        time.sleep(1)
        if not is_running(server_name):
            return 'stopped', 0
            
    try:
        subprocess.run(["screen", "-S", server_name, "-X", "quit"])
        return 'killed', 0
    except Exception as e:
        return str(e), 1703

def say_to_server(server_name, message):  # 19xx
    if helpers._is_empty(server_name):
        return '"server-name" is required', 1901
    if helpers._is_empty(server_name):
        return f'server not running "{server_name}"', 1902
    if helpers._is_empty(message):
        return '"message" is required', 1903
        
    result = send_command(server_name, f'say {message}')
    if result[1] == 0:
        return message, 0
    return 'unexpected error', 1904, result

def send_command(server_name, command):  # 20xx
    if helpers._is_empty(server_name):
        return '"server-name" is required', 2001
    if False == is_running(server_name):
        return f'server not running "{server_name}"', 2002
    if helpers._is_empty(command):
        return '"command" is required', 2003
    try:
        subprocess.run(["screen", "-Rd", server_name, "-X", "stuff", f'{command}\n'])
        return command, 0
    except Exception as e:
        return str(e), 2004

def get_created():
    try:
        directory_contents = os.listdir(settings.SERVER_PATH)
        directories = [entry for entry in directory_contents if os.path.isdir(os.path.join(settings.SERVER_PATH, entry))]
        
        return directories
    except OSError as e:
        logging.error(f"Fehler beim Lesen des Verzeichnisses: {e}")
        return []

def get_running():
    try:
        output = subprocess.check_output(['screen', '-list']).decode('utf-8')
        session_names = re.findall(r'\t\d+\.(.+?)\s+\(', output)

        return session_names
    except subprocess.CalledProcessError as e:
        logging.warning(str(e))
        return []

def is_running(server_name):
    if server_name in get_running():
        return True
    else:
        return False

def is_port_free(port):
    running_server = get_running()
    for server in running_server:
        properties_file = os.path.join(settings.SERVER_PATH, server, 'server.properties')
        properties = helpers.read_properties(properties_file)
        if properties[0]['server-port'] == port:
            return False
    return True

def get_server_version(server_name):  # 21xx
    version_file = os.path.join(settings.SERVER_PATH, server_name, 'version')
    try:
        with open(version_file, 'r') as file:
            version = file.read()
        return version, 0
    except FileNotFoundError:
        logging.error(f'file {version_file} not found')
        return f'version-file not found', 2101
    except Exception as e:
        logging.error(f'cannot read file {version_file}: {e}')
        return f'cannot read version-file: {e}', 2102

def parse_log(server_name):
    state = {
        "start_time": None,
        "started_time": None,
        "user_count": 0,
        "user_sessions": {},
        "stop_time": None,
        "last_server_state": None
    }
    
    log_file = os.path.join(settings.LOGS_PATH, server_name)
    if not os.path.exists(log_file):
        with open(log_file, 'x'):
            pass
        return {}

    with open(log_file, 'r') as file:
        for line in file:
            # Suche nach Zeilen mit Datum/Zeit im Format [YYYY-MM-DD HH:mm:ss:ms INFO]
            match = re.match(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}:\d{3}) INFO\]', line)
            if match:
                timestamp = datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S:%f')
                message = line[len(match.group(0)) + 1:].strip()

                # Serverstartzeit und -endzeit
                if "Starting Server" in message:
                    state = {
                        "start_time": timestamp,
                        "started_time": None,
                        "user_count": 0,
                        "user_sessions": {},
                        "stop_time": None,
                        "last_server_state": "Starting Server"
                    }
                elif "Server started" in message:
                    state['started_time'] = timestamp
                    state['last_server_state'] = "Server started"

                # User-Sitzungen
                if "Player connected" in message:
                    username = re.search(r'Player connected: (\w+)', message).group(1)
                    state['user_sessions'][username] = {'start': timestamp}
                    state['last_server_state'] = f"Player connected: {username}"
                    state['user_count'] = state['user_count'] + 1
                elif "Player disconnected" in message:
                    username = re.search(r'Player disconnected: (\w+)', message).group(1)
                    if username in state['user_sessions']:
                        state['user_sessions'][username]['end'] = timestamp
                        state['last_server_state'] = f"Player disconnected: {username}"
                        state['user_count'] = state['user_count'] - 1

                # Serverstoppzeit
                if "Server stop requested" in message:
                    state['stop_time'] = timestamp
                    state['last_server_state'] = "Server stop requested"

    return state

def get_worlds(server_name):  # 22xx
    if helpers._is_empty(server_name):
        return 'server-name is required', 2201
    
    worlds_path = os.path.join(settings.SERVER_PATH, server_name, 'worlds')
    try:
        directory_contents = os.listdir(worlds_path)
        directories = [entry for entry in directory_contents if os.path.isdir(os.path.join(worlds_path, entry))]
        
        return directories, 0
    except OSError as e:
        logging.error(f"cannot read server-worlds: {e}")
        return 'cannot read server-worlds', 2202

def get_world(server_name, level_name=None):  # 23xx
    if helpers._is_empty(server_name):
        return 'server-name is required', 2301
    
    result = get_worlds(server_name)
    if result[1] > 0:
        return 'error', 2302, result
    worlds = result[0]

    if len(worlds) == 0:
        return 'no worlds found', 2303
    elif level_name is not None:
        if level_name in worlds:
            return level_name, 0
        else:
            return 'the level-name does not exists in this server', 2304
    elif len(worlds) == 1:
        return worlds[0], 0
    else:
        return 'there is more than one world. you must enter a "level-name".', 2305
    
def remove_world(server_name, level_name=None):  # 24xx
    if helpers._is_empty(server_name):
        return 'server-name is required', 2401
    
    result = get_worlds(server_name)
    if result[1] > 0:
        return 'error', 2402, result
    worlds = result[0]

    if len(worlds) == 0:
        return 'no worlds found', 2403
    elif level_name is not None:
        if level_name in worlds:
            level_path = os.path.join(settings.SERVER_PATH, server_name, 'worlds', level_name)
            result = helpers.remove_dirtree(level_path)
            if result[1] > 0:
                return 'cannot remove world', 2404, result
            return 'successfully removed', 0
        else:
            return 'the level-name does not exists in this server', 2405
    elif len(worlds) == 1:
        return worlds[0], 0
    else:
        return 'there is more than one world. you must enter a "level-name".', 2406

