# server.py

from zipfile import ZipFile
from datetime import datetime

import helpers
import logging
import os
import re
import requests
import shutil
import subprocess
import time

DOWNLOADED_PATH = '/app/downloaded_server'
CREATED_PATH = '/app/created_server'
LOGS_PATH = '/app/logs'

def get_local_version(sourcefile):  # 13xx
    local_server_version = os.path.join(DOWNLOADED_PATH, sourcefile)
    try:
        with open(local_server_version, 'r') as file:
            version = file.read()

        logging.debug(f'content of {local_server_version}: {version}')
        return version, 0
    except FileNotFoundError:
        logging.error(f'file {local_server_version} not found')
        return f'{sourcefile}-file not found', 1301
    except Exception as e:
        logging.error(f'cannot read file {local_server_version}: {e}')
        return f'cannot read {sourcefile}-file: {e}', 1302

def get_online_version():  # 11xx
    headers = {'User-Agent': 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1)'}
    server_version_url = 'https://minecraft.net/de-de/download/server/bedrock/';

    try:
        response = requests.get(server_version_url, headers=headers)
        response.raise_for_status()

        if response.status_code == 200:
            matches = re.search(r'https://.+linux.+-([0-9\.]+).zip', response.text)
            if matches and len(matches.groups()) == 1:
        
                # set latest
                latest_server_version = os.path.join(DOWNLOADED_PATH, 'latest')
                with open(latest_server_version, 'w') as latest_file:
                    latest_file.write(matches.group(1))
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
        return 'version is required', 1201

    server_path = os.path.join(DOWNLOADED_PATH, version)
    if os.path.exists(server_path):
        logging.debug(f"server already exists: {server_path}")
        return f'server already exists: {version}', 0
    
    # create Download-Path
    if not os.path.exists(DOWNLOADED_PATH):
        os.mkdir(DOWNLOADED_PATH)
        os.chmod(DOWNLOADED_PATH, 0o777)
    
    # download
    zip_path = os.path.join(DOWNLOADED_PATH, f'bedrock-server-{version}.zip')
    if not os.path.exists(zip_path):
        try:
            url = f'https://minecraft.azureedge.net/bin-linux/bedrock-server-{version}.zip'
            response = requests.get(url, stream=True)
            response.raise_for_status()

            with open(zip_path, 'wb') as f:
                shutil.copyfileobj(response.raw, f)
        except Exception as e:
            logging.error(str(e))
            return str(e), 1202
    else:
        logging.debug(f"file already exists: {zip_path}")

    # unzip
    if not os.path.exists(server_path):
        with ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(server_path)
    else:
        logging.debug(f"dir already exists: {server_path}")
    
    # remove zip
    try:
        os.remove(zip_path)
    except OSError as e:
        logging.error(f"error at removing {zip_path}: {e}")
        
    # add version
    server_version_file = os.path.join(server_path, 'version')
    if not os.path.exists(server_version_file):
        with open(server_version_file, 'w') as version_file:
            version_file.write(version)
    else:
        logging.debug(f"server-version-file allready exists: {server_version_file}")
        
    # set downloaded
    downloaded_server_version = os.path.join(DOWNLOADED_PATH, 'downloaded')
    with open(downloaded_server_version, 'w') as downloaded_file:
        downloaded_file.write(version)
        
    return f'server downloaded: {version}', 0

def create(properties=[]):  # 14xx
    if 'server-name' in properties:
        server_name = properties['server-name']
    else:
        return 'server-name is required', 1401
            
    if 'server-version' in properties:
        server_version = properties['server-version']
        del properties['server-version']
    else:
        return 'server-version is required', 1402

    # create world-path
    if not os.path.exists(CREATED_PATH):
        os.mkdir(CREATED_PATH)
        os.chmod(CREATED_PATH, 0o777)

    # test server-path
    world_path = os.path.join(CREATED_PATH, server_name)
    server_path = os.path.join(DOWNLOADED_PATH, server_version)
    if not os.path.exists(server_path):
        logging.error(f"server-version not exists: {server_path}")
        return f'server-version not exists: {server_version}', 1403
    
    # copy server
    try:
        logging.debug(f'copy {server_path} to {world_path}')
        shutil.copytree(server_path, world_path)
        helpers.change_permissions_recursive(world_path, 0o777)
        logging.debug(f"successfully copied: {server_path} to {world_path}")
    except FileNotFoundError:
        logging.error(f"server not exists: {server_path}")
        return f'server not exists: {server_path}', 1404
    except FileExistsError:
        logging.error(f"world already exists: {world_path}")
        return f'world already exists: {world_path}', 1405
    except Exception as e:
        logging.error(f"unexpected error: {e}")
        return f'unexpected error: {e}', 1406
    
    # prepare world
    try:
        properties_file = os.path.join(world_path, 'server.properties')
        with open(properties_file, 'r') as file:
            lines = file.readlines()

        for key, value in properties.items():
            for i in range(len(lines)):
                if lines[i].startswith(f'{key}='):
                    logging.debug(f'prepare: {key}={value}')
                    lines[i] = f'{key}={value}\n'

        with open(properties_file, 'w') as file:
            file.writelines(lines)

        logging.debug(f'successfully prepared {properties_file}')
    except FileNotFoundError:
        logging.error(f'properties-file not found: {properties_file}')
        return f'properties-file not found', 1407
    except Exception as e:
        logging.error(f"unexpected error: {e}")
        return f'unexpected error: {e}', 1408
        
    return f'{server_name}', 0

def remove(server_name=None):  # 15xx
    if helpers._is_empty(server_name):
        return 'server-name is required', 1501
    
    try:
        world_path = os.path.join(CREATED_PATH, server_name)
        shutil.rmtree(world_path)
        log_file = os.path.join(LOGS_PATH, server_name)
        os.remove(log_file)
        logging.debug(f'successfully removed {world_path}')
        return f'{server_name}', 0
    except FileNotFoundError:
        logging.error(f"world not exists: {world_path}")
        return f'world not exists: {server_name}', 1502
    except PermissionError:
        logging.error(f"canot remove world: {world_path}")
        return f'canot remove world: {server_name}', 1503
    except Exception as e:
        logging.error(f"unexpected error: {e}")
        return f'unexpected error: {e}', 1504

def start(server_name=None, server_port=None):  # 16xx
    if helpers._is_empty(server_name):
        return 'server-name is required', 1601
    if helpers._is_empty(server_port):
        return 'server-port is required', 1602
        
    world_path = os.path.join(CREATED_PATH, server_name)
    if not os.path.exists(world_path):
        return 'server-name does not exists', 1603
        
    if is_running(server_name):
        return 'server is already running', 1608
        
    if server_port == None:
        return 'server-port is using', 1604
    
    try:
        properties_file = os.path.join(world_path, 'server.properties')
        with open(properties_file, 'r') as file:
            lines = file.readlines()

        for i in range(len(lines)):
            if lines[i].startswith(f'server-port='):
                logging.debug(f'prepare: server-port={server_port}')
                lines[i] = f'server-port={server_port}\n'

        with open(properties_file, 'w') as file:
            file.writelines(lines)

        logging.debug(f'successfully prepared {properties_file}')
    except FileNotFoundError:
        logging.error(f'properties-file not found: {properties_file}')
        return f'properties-file not found', 1605
    except Exception as e:
        logging.error(f"unexpected error: {e}")
        return f'unexpected error: {e}', 1606

    # create logs-path
    if not os.path.exists(LOGS_PATH):
        os.mkdir(LOGS_PATH)
        os.chmod(LOGS_PATH, 0o777)
        
    try:
        server_log = os.path.join(LOGS_PATH, server_name)
        os.remove(server_log)
        subprocess.run([
            'screen',
            '-dmS', server_name,
            '-L', '-Logfile', server_log,
            'bash', '-c', f'cd {world_path} ; LD_LIBRARY_PATH=. ; ./bedrock_server'
        ])

    except Exception as e:
        logging.error(f"unexpected error: {e}")
        return f'unexpected error: {e}', 1607

    for i in range(60):
        time.sleep(1)
        states = parse_log(server_name)
        if states['start_time'] and states['started_time'] and states['start_time'] < states['started_time']:
            logging.debug(f'successfully started {server_name}')
            return f'{server_name}', 0
        logging.debug(f'starting {server_name}')
            
    subprocess.run(["screen", "-S", server_name, "-X", "quit"])
    return f'cannot start server: {server_name}', 1608

def list():
    created_server = get_created()
    if len(created_server) == 0:
        return 'no server created', 0
    
    running_server = get_running()
    result = {
        "count-created-server": len(created_server),
        "count-running-server": len(running_server)
    }
    for created_server in created_server:
        properties = read_properties(created_server)
        states = parse_log(created_server)
        result[created_server] = {
            "server-name": created_server,
            "is-running": created_server in running_server,
            "server-port": properties[0]['server-port'] if properties[1] == 0 else None,
            "level-name": properties[0]['level-name'] if properties[1] == 0 else None,
            "states": states
        }
    return result, 0

def stop(server_name, wait_for_disconnected_user=False):  # 17xx
    if helpers._is_empty(server_name):
        return 'server-name is required', 1701
        
    world_path = os.path.join(CREATED_PATH, server_name)
    if not is_running(server_name):
        return 'already stopped', 0

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
        # Verzeichnisinhalt auflisten
        directory_contents = os.listdir(CREATED_PATH)
        
        # Nur Verzeichnisse filtern
        directories = [entry for entry in directory_contents if os.path.isdir(os.path.join(CREATED_PATH, entry))]
        
        return directories
    except OSError as e:
        logging.error(f"Fehler beim Lesen des Verzeichnisses: {e}")
        return []

def get_running():
    try:
        # Führe das Shell-Kommando aus und lese die Ausgabe
        output = subprocess.check_output(['screen', '-list']).decode('utf-8')

        # Verwende reguläre Ausdrücke, um die Session-IDs zu extrahieren
        session_names = re.findall(r'\t\d+\.(.+?)\s+\(', output)

        return session_names
    except subprocess.CalledProcessError as e:
        logging.warning(str(e))
        return []

def read_properties(server_name):  # 18xx
    properties = {}
    world_path = os.path.join(CREATED_PATH, server_name)
    try:
        properties_file = os.path.join(world_path, 'server.properties')
        with open(properties_file, 'r') as file:
            for line in file:
                # Entferne Leerzeichen und Zeilenumbrüche
                line = line.strip()
                # Ignoriere Kommentarzeilen
                if not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)  # Nur die erste '=' wird beachtet
                    properties[key.strip()] = value.strip()
    except FileNotFoundError:
        logging.error(f"Die Datei '{properties_file}' wurde nicht gefunden.")
        return f'properties-file not found', 1801
    except Exception as e:
        logging.error(f"Fehler beim Lesen der Datei '{properties_file}': {e}")
        return str(e), 1802
    return properties, 0

def parse_log(server_name):
    state = {
        "start_time": None,
        "started_time": None,
        "user_count": 0,
        "user_sessions": {},
        "stop_time": None,
        "last_server_state": None
    }
    
    log_file = os.path.join(LOGS_PATH, server_name)
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

def is_running(server_name):
    if server_name in get_running():
        return True
    else:
        return False
