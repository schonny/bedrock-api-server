# helpers.py

import os

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
