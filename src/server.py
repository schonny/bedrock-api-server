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

def get_local_version(sourcefile):  # 13xx
    local_server_version = os.path.join(settings.DOWNLOADED_PATH, sourcefile)
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
                latest_server_version = os.path.join(settings.DOWNLOADED_PATH, 'latest')
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
        result = get_online_version()
        if result[1] == 0:
            version = result[0]
        else:
            return 'cannot get online-version', 1201, result

    server_path = os.path.join(settings.DOWNLOADED_PATH, version)
    if os.path.exists(server_path):
        logging.debug(f"server already exists: {server_path}")
        return f'server already exists: {version}', 0
    
    # download
    zip_path = os.path.join(settings.DOWNLOADED_PATH, f'{version}.zip')
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
        
    # set downloaded
    downloaded_server_version = os.path.join(settings.DOWNLOADED_PATH, 'downloaded')
    with open(downloaded_server_version, 'w') as downloaded_file:
        downloaded_file.write(version)
        
    return f'server downloaded: {version}', 0

def create(static_properties={}):  # 14xx
    if 'server-name' in static_properties:
        server_name = static_properties['server-name']
    else:
        return 'server-name is required', 1401
            
    if 'server-version' in static_properties:
        server_version = static_properties['server-version']
    else:
        result = get_local_version('downloaded')
        if result[1] == 0:
            server_version = result[0]
            static_properties['server-version'] = server_version
        else:
            return 'a server must be downloaded first.', 1403, result

    # unzip to server-path
    zip_path = os.path.join(settings.DOWNLOADED_PATH, f'{server_version}.zip')
    server_path = os.path.join(settings.SERVER_PATH, server_name)
    if not os.path.exists(zip_path):
        return 'this server version does not exist.', 1404, result
    if not os.path.exists(server_path):
        with ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(server_path)
    else:
        logging.debug(f"server already exists: {server_path}")
        return f'server already exists: {server_path}', 1405
    
    # write statics.properties
    try:
        statics_properties_file = os.path.join(server_path, 'static.properties')
        with open(statics_properties_file, 'w') as file:
            for key, value in static_properties.items():
                file.write(f'{key}={value}\n')
        logging.debug('static.properties created')
    except Exception as e:
        logging.error(f"unexpected error: {e}")
        return str(e), 1406
        
    helpers.change_permissions_recursive(server_path, 0o777)
    return f'{server_name}', 0

def remove(server_name=None):  # 15xx
    if helpers._is_empty(server_name):
        return 'server-name is required', 1501
    
    try:
        server_path = os.path.join(settings.SERVER_PATH, server_name)
        shutil.rmtree(server_path)
        log_file = os.path.join(settings.LOGS_PATH, server_name)
        os.remove(log_file)
        logging.debug(f'successfully removed {server_path}')
        return f'{server_name}', 0
    except FileNotFoundError:
        logging.error(f"world not exists: {server_path}")
        return f'world not exists: {server_name}', 1502
    except PermissionError:
        logging.error(f"canot remove world: {server_path}")
        return f'canot remove world: {server_name}', 1503
    except Exception as e:
        logging.error(f"unexpected error: {e}")
        return f'unexpected error: {e}', 1504

def start(start_properties={}):  # 16xx
    if 'server-name' in start_properties:
        server_name = start_properties['server-name']
    else:
        return 'server-name is required', 1601

    server_path = os.path.join(settings.SERVER_PATH, server_name)
    if not os.path.exists(server_path):
        return 'server with this name does not exists', 1602
        
    if is_running(server_name):
        return 'server already running', 0
    
    # read static.properties
    try:
        static_properties_file = os.path.join(server_path, 'static.properties')
        static_properties = read_properties(static_properties_file)[0]
    except Exception as e:
        logging.error(f"unexpected error: {e}")
        return f'unexpected error: {e}', 1603
    
    # merge properties (server > start > static)
    try:
        server_properties_file = os.path.join(server_path, 'server.properties')
        server_properties = read_properties(server_properties_file)[0]
        # merge
        for key, value in server_properties.items():
            if key in static_properties:
                server_properties[key] = static_properties[key]
            elif key in start_properties:
                server_properties[key] = start_properties[key]

        # check server-port
        if not is_port_free(server_properties['server-port']):
            return f'server-port is already in use: {server_properties['server-port']}', 1604
    
        # write server.properties
        with open(server_properties_file, 'w') as file:
            for key, value in server_properties.items():
                file.write(f'{key}={value}\n')

        logging.debug('successfully merged properties')
    except Exception as e:
        logging.error(f"unexpected error: {e}")
        return f'unexpected error: {e}', 1605
    
    # start server in screen-session
    try:
        server_log = os.path.join(settings.LOGS_PATH, server_name)
        os.remove(server_log)
        subprocess.run([
            'screen',
            '-dmS', server_name,
            '-L', '-Logfile', server_log,
            'bash', '-c', f'cd {server_path} ; LD_LIBRARY_PATH=. ; ./bedrock_server'
        ])
    except Exception as e:
        logging.error(f"unexpected error: {e}")
        return f'unexpected error: {e}', 1607

    # wait for running
    for i in range(60):
        time.sleep(1)
        states = parse_log(server_name)
        if states['start_time'] and states['started_time'] and states['start_time'] < states['started_time']:
            logging.debug(f'successfully started {server_name}')
            return f'{server_name}', 0
        logging.debug(f'starting {server_name}')

    # abourt
    # ToDo: return server-log
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
    for server_name in created_server:
        properties_file = os.path.join(settings.SERVER_PATH, server_name, 'server.properties')
        print(properties_file)
        properties = read_properties(properties_file)
        states = parse_log(server_name)
        result[server_name] = {
            "server-name": server_name,
            "is-running": server_name in running_server,
            "server-port": properties[0]['server-port'] if properties[1] == 0 else None,
            "level-name": properties[0]['level-name'] if properties[1] == 0 else None,
            "states": states
        }
    return result, 0

def stop(server_name, wait_for_disconnected_user=False):  # 17xx
    if helpers._is_empty(server_name):
        return 'server-name is required', 1701
        
    world_path = os.path.join(settings.SERVER_PATH, server_name)
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
        directory_contents = os.listdir(settings.SERVER_PATH)
        
        # Nur Verzeichnisse filtern
        directories = [entry for entry in directory_contents if os.path.isdir(os.path.join(settings.SERVER_PATH, entry))]
        
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

def is_running(server_name):
    if server_name in get_running():
        return True
    else:
        return False

def is_port_free(port):
    running_server = get_running()
    for server in running_server:
        properties_file = os.path.join(settings.SERVER_PATH, server, 'server.properties')
        properties = read_properties(properties_file)
        if properties[0]['server-port'] == port:
            return False
    return True

def read_properties(file):  # 18xx
    properties = {}
    try:
        with open(file, 'r') as file:
            for line in file:
                # Entferne Leerzeichen und Zeilenumbrüche
                line = line.strip()
                # Ignoriere Kommentarzeilen
                if not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)  # Nur die erste '=' wird beachtet
                    properties[key.strip()] = value.strip()
    except FileNotFoundError:
        logging.error(f"properties-file not found '{file}'")
        return f'properties-file not found', 1801
    except Exception as e:
        logging.error(f"unexpected error '{file}': {e}")
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
