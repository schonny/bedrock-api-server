# helpers.py
# err:40xx

from datetime import datetime
import concurrent.futures
import json
import logging
import os
import random
import re
import shutil
import string
import subprocess

def is_true(value):
    if isinstance(value, str):
        return value.lower() in ["true", "yes", "on", "1"]
    return bool(value)

def is_false(value):
    if isinstance(value, str):
        return value.lower() in ["false", "no", "off", "0", "-1"]
    return not bool(value)
      
def is_empty(value):
    return value == None or value == "" or (not isinstance(value, datetime) and len(value) == 0)

def change_permissions_recursive(directory_path, mode):
    os.chmod(directory_path, mode)
    for root, dirs, files in os.walk(directory_path):
        for dir_path in [os.path.join(root, d) for d in dirs]:
            os.chmod(dir_path, mode)
        for file_path in [os.path.join(root, f) for f in files]:
            os.chmod(file_path, mode)

def read_properties(file):  # 401x
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
        return f'properties-file not found', 4011
    except Exception as e:
        logging.error(f"unexpected error '{file}': {e}")
        return str(e), 4012
    return properties, 0

def merge_properties(infiles, outfile=None):  # 402x
    out_properties = {}

    # read
    for infile in infiles:
        try:
            infile_result = read_properties(infile)
            if infile_result[1] == 0:
                properties = infile_result[0]
                for key, value in properties.items():
                    out_properties[key] = value
            else:
                return 'cannot read file', 4021, infile_result
        except Exception as e:
            logging.error(f"unexpected error: {e}")
            return str(e), 4022
    
    if outfile == None:
        return out_properties, 0
    
    result = write_properties(outfile, out_properties)
    return outfile, 0 if result[1] == 0 else 'cannot write properties-file', 4023, result

def write_properties(property_file, properties=None):  # 403x
    try:
        with open(property_file, 'w') as file:
            for key, value in properties.items():
                file.write(f'{key}={value}\n')
        os.chmod(property_file, 0o777)
        logging.debug('successfully write properties')
        return file, 0
    except Exception as e:
        logging.error(f"unexpected error: {e}")
        return str(e), 4031

def remove_dirtree(path):  # 404x
    try:
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)
        logging.debug(f'successfully removed {path}')
        return f'removed {path}', 0
    except FileNotFoundError:
        logging.error(f"dir not exists: {path}")
        return f'dir not exists: {path}', 4043
    except PermissionError:
        logging.error(f"canot remove dir: {path}")
        return f'canot remove dir: {path}', 4044
    except Exception as e:
        logging.error(f"unexpected error: {e}")
        return str(e), 4045

def parallel(process, parameters):  # 405x
    if isinstance(parameters, set):
        parameters = [*parameters, ]
    results = []
    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = {executor.submit(process, parameters[i]): i for i in range(len(parameters))}
        for future in concurrent.futures.as_completed(futures):
            i = futures[future]
            results.append({
                'index': i,
                'parameters': parameters[i],
                'result': future.result()
            })
    return results

def screen_start(screen_name, bash_command, log_file):  # 406x
    try:
        result = subprocess.run(['screen', '-dmS', screen_name, '-L', '-Logfile', log_file, 'bash', '-c', bash_command], capture_output=True, text=True)
        if result.returncode > 0:
            return 'error at starting', 4061
        return {
            'state': 'started'
        }, 0
    except Exception as e:
        logging.error(f"unexpected error: {e}")
        return str(e), 4062

def screen_stop(screen_name):  # 407x
    try:
        result = subprocess.run(["screen", "-S", screen_name, "-X", "quit"], stderr=subprocess.DEVNULL)
        return {
            'state': 'stopped' if result.returncode == 0 else 'already stopped'
        }, 0
    except subprocess.CalledProcessError as e:
        return str(e), 4071

def screen_command(screen_name, command):  # 408x
    try:
        result = subprocess.run(["screen", "-Rd", screen_name, "-X", "stuff", f'{command}\n'])
        return {
            'state': 'sent' if result.returncode == 0 else 'failed'
        }, 0
    except subprocess.CalledProcessError as e:
        return str(e), 4081

def screen_list():  # 409x
    try:
        result = subprocess.check_output(['screen', '-list'], stderr=subprocess.DEVNULL).decode('utf-8')
        return re.findall(r'\t\d+\.(.+?)\s+\(', result)
    except subprocess.CalledProcessError as e:
        return []

def screen_wipe():
    try:
        subprocess.check_output(['screen', '-wipe'], stderr=subprocess.DEVNULL).decode('utf-8')
        return True
    except subprocess.CalledProcessError as e:
        return False

def read_json(file_path):  # 410x
    data = {}
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        logging.error(f"json-file not found '{file_path}'")
        return f'json-file not found', 4101
    except Exception as e:
        logging.error(f"unexpected error '{file_path}': {e}")
        return str(e), 4102
    return data, 0

def write_json(file_path, data=None):  # 411x
    try:
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=2)
        os.chmod(file_path, 0o777)
        logging.debug('successfully write json')
        return file, 0
    except Exception as e:
        logging.error(f"unexpected error '{file_path}': {e}")
        return str(e), 4111

def rnd(length):  # 412x
    return ''.join(random.choices(string.ascii_letters, k=length))