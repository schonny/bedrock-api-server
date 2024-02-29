# server.py

from zipfile import ZipFile
from datetime import datetime
import logging
import os
import re
import requests
import shutil
import subprocess
import time

import helpers
import settings
import world

def get_online_version(preview=None):  # 110x
    headers = {'User-Agent': 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1)'}
    version_url = 'https://minecraft.net/de-de/download/server/bedrock/';

    try:
        response = requests.get(version_url, headers=headers)
        response.raise_for_status()

        if response.status_code == 200:
            zip_url = r'https://.+linux.+-([0-9\.]+).zip'
            if helpers.is_true(preview):
                zip_url = r'https://.+linux-preview.+-([0-9\.]+).zip'

            matches = re.search(zip_url, response.text)
            if matches and len(matches.groups()) == 1:
                return {
                    "branch": "stable" if helpers.is_false(preview) else "preview",
                    "version": matches.group(1)
                }, 0
            else:
                logging.error('Error: result cannot be parsed')
                return 'result cannot be parsed', 1101
        else:
            logging.error('Error: cat not read from external server')
            return 'cannot read from external server', 1102
                
    except Exception as e:
        logging.error(f"Error: {e}")
        return str(e), 1103

def download(version=None):  # 111x
    if helpers.is_empty(version):
        result = get_online_version()
        if result[1] == 0:
            version = result[0]['version']
        else:
            return 'cannot get online-version', 1111, result

    zip_path = os.path.join(settings.DOWNLOADED_PATH, f'{version}.zip')
    if os.path.exists(zip_path):
        logging.debug(f"server already downloaded: {zip_path}")
        return {
            'version': version,
            'state': 'already downloaded'
        }, 0
    
    def _download(url, zip_path):
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()

            with open(zip_path, 'wb') as f:
                shutil.copyfileobj(response.raw, f)
            logging.debug(f"downloaded: {url}")
            return True
        except Exception as e:
            logging.error(str(e))
            return False

    if not os.path.exists(zip_path):
        url = f'https://minecraft.azureedge.net/bin-linux/bedrock-server-{version}.zip'
        branch = 'stable'
        if not _download(url, zip_path):
            url = f'https://minecraft.azureedge.net/bin-linux-preview/bedrock-server-{version}.zip'
            branch = 'preview'
            if not _download(url, zip_path):
                if os.path.exists(zip_path):
                    os.remove(zip_path)
                return f'cannot download version {version}', 1112
        
        helpers.change_permissions_recursive(zip_path, 0o777)
        state = 'downloaded'
    else:
        logging.debug(f"file already exists: {zip_path}")
        state = 'already exists'

    return {
        'version': version,
        'state': state,
        'branch': branch
    }, 0

def get_downloaded_versions():  # 112x
    try:
        files = os.listdir(settings.DOWNLOADED_PATH)
        versions = [os.path.splitext(file)[0] for file in files if file.endswith('.zip')]
        if len(versions) > 0:
            versions = sorted(versions, key=lambda x: [int(part) for part in x.split('.')], reverse=True)
        return {
            'versions': versions,
            'count': len(versions)
        }, 0
    except Exception as e:
        logging.error(f"cannot read filesystem: {e}")
        return str(e), 1121

def create(default_properties=None):  # 113x
    if not isinstance(default_properties, dict):
        return 'parameter must be a object', 1131
        
    if 'server-name' in default_properties and len(default_properties['server-name']) > 0:
        server_name = default_properties['server-name']
    else:
        return 'server-name is required', 1132
            
    if 'version' in default_properties:
        version = default_properties['version']
        del default_properties['version']
    else:
        result = get_downloaded_versions()
        if result[1] == 0 and result[0]['count'] > 0:
            version = result[0]['versions'][0]
        else:
            return 'a server must be downloaded first.', 1133, result

    # unzip to server-path
    zip_path = os.path.join(settings.DOWNLOADED_PATH, f'{version}.zip')
    server_path = os.path.join(settings.SERVER_PATH, server_name)
    if not os.path.exists(zip_path):
        return 'this server version does not exist.', 1134
    if not os.path.exists(server_path):
        with ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(server_path)
    else:
        logging.debug(f"server already exists: {server_path}")
        return f'server already exists: {server_name}', 1135
        
    # set version
    version_file = os.path.join(server_path, 'version')
    with open(version_file, 'w') as version_file:
        version_file.write(version)
    
    # write server_default.properties
    result = helpers.write_properties(os.path.join(server_path, 'server_default.properties'), default_properties)
    if result[1] > 0:
        return 'error at write server_default.properties', 1136, result
    
    # rename server.properties > server_old.properties
    os.rename(os.path.join(server_path, 'server.properties'), os.path.join(server_path, 'server_old.properties'))

    helpers.change_permissions_recursive(server_path, 0o777)
    return {
        'server-name': server_name,
        'version': version,
        'default-properties': default_properties
    }, 0

def remove(server_name=None):  # 114x
    if helpers.is_empty(server_name):
        return 'server-name is required', 1141
    
    if server_name not in get_created():
        return 'server does not exists', 1142
    
    if is_running(server_name):
        return 'this server is running', 1143
    
    # remove server
    server_path = os.path.join(settings.SERVER_PATH, server_name)
    result = helpers.remove_dirtree(server_path)
    if result[1] > 0:
        return 'cannot remove server', 1144, result

    # remove log
    try:
        os.remove(os.path.join(settings.LOGS_PATH, server_name))
        logging.debug(f'successfully removed {server_path}')
    except Exception as e:
        logging.error(f"unexpected error: {e}")
        return str(e), 1145
    
    return {
        'server-name': server_name,
        'state': 'removed'
    }, 0

def start(start_properties=None):  # 115x
    if not isinstance(start_properties, dict):
        return 'parameter must be a object', 1151

    if 'server-name' in start_properties:
        server_name = start_properties['server-name']
    else:
        return 'server-name is required', 1152

    server_path = os.path.join(settings.SERVER_PATH, server_name)
    if not os.path.exists(server_path):
        return f"server with this name '{server_name}' does not exists", 1153

    if is_running(server_name):
        return {
            'server-name': server_name,
            'state': 'already running'
        }, 0
    
    # write server_start.properties
    result = helpers.write_properties(os.path.join(server_path, 'server_start.properties'), start_properties)
    if result[1] > 0:
        return 'error at write server_start.properties', 1154, result
    
    result = start_simple(server_name)
    return result[0], 0 if result[1] == 0 else 'cannot start server', 1155, result

def stop(server_name=None, wait_for_disconnected_user=False):  # 116x
    if helpers.is_empty(server_name):
        return 'server-name is required', 1161
        
    if not is_running(server_name):
        return {
            'server-name': server_name,
            'state':'nothing to stop',
            'times': 0
        }, 0

    sec = 5
    start_time = time.time()
    log_result = parse_log(server_name)
    if wait_for_disconnected_user:
        say_stop = 0
        while log_result[1] == 0 and 'user-count' in log_result[0] and log_result[0]['user-count'] > 0:
            if say_stop <= 0:
                say_stop = 60 // sec
                say_to_server(server_name, 'This server is supposed to be shut down. Please finish your game.')
            say_stop -= sec
            time.sleep(sec)
            log_result = parse_log(server_name)

    elif log_result[1] == 0 and 'user-count' in log_result[0] and log_result[0]['user-count'] > 0:
        say_to_server(server_name, 'This server will shutdown in 1 minute. Please finish your game.')
        for i in range(60 // sec, 0, -1):
            log_result = parse_log(server_name)
            if log_result[1] == 0 and log_result[0]['user-count'] <= 0:
                break
            if i * sec in [30, 20, 10]:
                say_to_server(server_name, f'This server will shutdown in {i * sec} seconds. Please finish your game.')
            time.sleep(sec)
            
    result = send_command(server_name, 'stop')
    if result[1] != 0:
        return 'cannot send stop-command', 1162, result

    for i in range(60):
        time.sleep(1)
        if not is_running(server_name):
            return {
                'server-name': server_name,
                'state': 'stopped',
                'times': int(time.time() - start_time)
            }, 0
            
    try:
        subprocess.run(["screen", "-S", server_name, "-X", "quit"], stderr=subprocess.DEVNULL)
        return {
            'server-name': server_name,
            'state': 'killed',
            'times': int(time.time() - start_time)
        }, 0
    except Exception as e:
        return str(e), 1163

def say_to_server(server_name=None, message=None):  # 117x
    if helpers.is_empty(server_name):
        return '"server-name" is required', 1171
    if not is_running(server_name):
        return f'server not running "{server_name}"', 1172
    if helpers.is_empty(message):
        return '"message" is required', 1173
        
    result = send_command(server_name, f'say {message}')
    if result[1] == 0:
        return {
            'server-name': server_name,
            'message': message
        }, 0
    return 'unexpected error', 1174, result

def send_command(server_name=None, command=None):  # 118x
    if helpers.is_empty(server_name):
        return '"server-name" is required', 1181
    if not is_running(server_name):
        return f'server not running "{server_name}"', 1182
    if helpers.is_empty(command):
        return '"command" is required', 1183
    try:
        subprocess.run(["screen", "-Rd", server_name, "-X", "stuff", f'{command}\n'])
        return {
            'server-name': server_name,
            'command': command
        }, 0
    except Exception as e:
        return str(e), 1184

def get_created():
    try:
        directory_contents = os.listdir(settings.SERVER_PATH)
        return [entry for entry in directory_contents if os.path.isdir(os.path.join(settings.SERVER_PATH, entry))]
    except OSError as e:
        logging.error(f"Fehler beim Lesen des Verzeichnisses: {e}")
        return []

def get_running():
    try:
        output = subprocess.check_output(['screen', '-list'], stderr=subprocess.DEVNULL).decode('utf-8')
        return re.findall(r'\t\d+\.(.+?)\s+\(', output)
    except subprocess.CalledProcessError as e:
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

def get_version(server_name):  # 119x
    version_file = os.path.join(settings.SERVER_PATH, server_name, 'version')
    try:
        with open(version_file, 'r') as file:
            version = file.read()
        return {
            'server-name': server_name,
            'version': version
        }, 0
    except FileNotFoundError:
        logging.error(f'file {version_file} not found')
        return f'version-file not found', 1191
    except Exception as e:
        logging.error(f'cannot read file {version_file}: {e}')
        return f'cannot read version-file: {e}', 1192

def parse_log(server_name=None):  # 120x
    if helpers.is_empty(server_name):
        return '"server-name" is required', 1201
    
    log_file = os.path.join(settings.LOGS_PATH, server_name)
    if not os.path.exists(log_file):
        return 'no log found', 1202
    
    state = {
        'server-name': server_name
    }

    with open(log_file, 'r') as file:
        for line in file:
            # Suche nach Zeilen mit Datum/Zeit im Format [YYYY-MM-DD HH:mm:ss:ms INFO]
            match = re.match(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}:\d{3}) INFO\]', line)
            if match:
                timestamp = datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S:%f')
                message = line[len(match.group(0)) + 1:].strip()

                if "Starting Server" in message:
                    state = {
                        'server-name': server_name,
                        "start-time": str(timestamp),
                        "state": "starting"
                    }
                elif "Server started" in message:
                    state['started-time'] = str(timestamp)
                    state['state'] = "started"
                elif "Level Name" in message:
                    state['level-name'] = re.search(r'Level Name: (.+)', message).group(1)
                elif "Game mode" in message:
                    state['gamemode'] = re.search(r'Game mode: (.+)', message).group(1)
                elif "Difficulty" in message:
                    state['difficulty'] = re.search(r'Difficulty: (.+)', message).group(1)
                elif "Player connected" in message:
                    if 'user-sessions' not in state:
                        state['user-sessions'] = {}
                    if 'user-count' not in state:
                        state['user-count'] = 0
                    user_name = re.search(r'Player connected: (\w+)', message).group(1)
                    state['user-sessions'][user_name] = {'start': str(timestamp)}
                    state['user-count'] += 1
                    state['state'] = "connected"
                elif "Player disconnected" in message:
                    user_name = re.search(r'Player disconnected: (\w+)', message).group(1)
                    if 'user-sessions' not in state and user_name in state['user-sessions']:
                        state['user-sessions'][user_name]['end'] = str(timestamp)
                        state['user-count'] -= 1
                        state['state'] = 'connected' if state['user-count'] > 0 else 'disconnected'
                elif "Server stop requested" in message:
                    state['stop-time'] = str(timestamp)
                    state['state'] = "stopped"

    return state, 0

def start_simple(server_name=None): # 124x
    if helpers.is_empty(server_name):
        return 'server-name is required', 1241

    server_path = os.path.join(settings.SERVER_PATH, server_name)
    if not os.path.exists(server_path):
        return f"server with this name '{server_name}' does not exists", 1242
    
    start_time = time.time()
    if is_running(server_name):
        return {
            'server-name': server_name,
            'state': 'already running',
            'times': 0
        }, 0
    
    if not os.path.exists(os.path.join(server_path, 'server.properties')) or (\
    os.path.exists(os.path.join(server_path, 'server_start.properties')) and (\
    os.path.getctime(os.path.join(server_path, 'server.properties')) < os.path.getctime(os.path.join(server_path, 'server_start.properties')))):
        # merge properties if server.properties not exists
        to_merge_files = [
            os.path.join(server_path, 'server_old.properties'),
            os.path.join(server_path, 'server_default.properties')
        ]
        if os.path.exists(os.path.join(server_path, 'server_start.properties')):
            to_merge_files.append(os.path.join(server_path, 'server_start.properties'))
        result = helpers.merge_properties(to_merge_files, os.path.join(server_path, 'server.properties'))
        if result[1] > 0:
            logging.error("cannot merge property-files")
            return "cannot merge property-files", 1243, result
    
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
        return str(e), 1244

    # wait for running
    for i in range(60):
        time.sleep(1)
        log_result = parse_log(server_name)
        states = log_result[0] if log_result[1] == 0 else {}
        if 'start-time' in states and 'started-time' in states and states['start-time'] and states['started-time'] and states['start-time'] < states['started-time']:
            logging.debug(f'successfully started {server_name}')
            version_result = get_version(server_name)
            return {
                'server-name': server_name,
                'version': version_result[0]['version'] if version_result[1] == 0 else 'unknown',
                'state': 'started',
                'times': int(time.time() - start_time),
                'log': states
            }, 0
        logging.debug(f'starting {server_name}')

    # abourt
    subprocess.run(["screen", "-S", server_name, "-X", "quit"], stderr=subprocess.DEVNULL)
    return f'cannot start server: {server_name}', 1245    

def start_all():  # 125x
    states = {
        'started': [],
        'already running': [],
        'failed': []
    }
    for sub_result in helpers.parallel(start_simple, set(get_created() + get_running())):
        server_name = sub_result['parameters']
        result = sub_result['result']
        if result[1] == 0:
            if result[0]['state'] == 'started':
                states['started'].append(server_name)
            else:
                states['already running'].append(server_name)
        else:
            states['failed'].append(server_name)
    return states, 0

def stop_all():  # 126x
    states = {
        'stopped': [],
        'already stopped': [],
        'failed': []
    }
    for sub_result in helpers.parallel(stop, set(get_created() + get_running())):
        server_name = sub_result['parameters']
        result = sub_result['result']
        if result[1] == 0:
            if result[0]['state'] == 'stopped':
                states['stopped'].append(server_name)
            else:
                states['already stopped'].append(server_name)
        else:
            states['failed'].append(server_name)
    return states, 0

def list():  # 127x
    return {
        "created-server": get_created(),
        "running-server": get_running()
    }, 0

def details(server_name=None):  # 128x
    if helpers.is_empty(server_name):
        return 'server-name is required', 1281

    server_path = os.path.join(settings.SERVER_PATH, server_name)
    if not os.path.exists(server_path):
        return f"server with this name '{server_name}' does not exists", 1282
    
    details = {
        'server-name': server_name
    }
    result = get_version(server_name)
    details['version'] = result[0]['version'] if result[1] == 0 else 'unknown'
    result = world.get_worlds(server_name)
    details['worlds'] = result[0]['worlds'] if result[1] == 0 else []
    result = parse_log(server_name)
    details['log'] = result[0] if result[1] == 0 else {}

    if len(details['worlds']) == 0:
        details['state'] = 'created'
    elif is_running(server_name):
        details['state'] = 'started'
    else:
        details['state'] = 'stopped'

    # properties
    if os.path.exists(os.path.join(settings.SERVER_PATH, server_name, 'server.properties')):
        result = helpers.read_properties(os.path.join(settings.SERVER_PATH, server_name, 'server.properties'))
    else:
        to_merge_files = [
            os.path.join(settings.SERVER_PATH, server_name, 'server_old.properties'),
            os.path.join(settings.SERVER_PATH, server_name, 'server_default.properties')
        ]
        if os.path.exists(os.path.join(settings.SERVER_PATH, server_name, 'server_start.properties')):
            to_merge_files.append(os.path.join(settings.SERVER_PATH, server_name, 'server_start.properties'))
        result = helpers.merge_properties(to_merge_files)
    details['properties'] = result[0] if result[1] == 0 else {}

    return details, 0
