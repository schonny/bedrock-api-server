# helpers.py

import logging
import os
import shutil

def _is_true(value):
    return value == True or value.lower() == "true" or value == 1 or value.lower() == "yes" or value.lower() == "on"

def _is_false(value):
    return value == False or value.lower() == "false" or value == 0 or value.lower() == "no" or value.lower() == "off"
      
def _is_empty(value):
    return value == None or value == "" or len(value) == 0

def change_permissions_recursive(directory_path, mode):
    os.chmod(directory_path, mode)
    for root, dirs, files in os.walk(directory_path):
        for dir_path in [os.path.join(root, d) for d in dirs]:
            os.chmod(dir_path, mode)
        for file_path in [os.path.join(root, f) for f in files]:
            os.chmod(file_path, mode)

def read_properties(file):  # 41xx
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
        return f'properties-file not found', 4101
    except Exception as e:
        logging.error(f"unexpected error '{file}': {e}")
        return str(e), 4102
    return properties, 0

def remove_dirtree(path):  # 42xx
    try:
        shutil.rmtree(path)
        logging.debug(f'successfully removed {path}')
        return f'removed {path}', 0
    except FileNotFoundError:
        logging.error(f"dir not exists: {path}")
        return f'dir not exists: {path}', 4203
    except PermissionError:
        logging.error(f"canot remove dir: {path}")
        return f'canot remove dir: {path}', 4204
    except Exception as e:
        logging.error(f"unexpected error: {e}")
        return str(e), 4205