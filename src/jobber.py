# jobber.py
# err:41xx

import json
import os
import re
import subprocess
import time
import yaml

import helpers
import settings

JOBBER_SCREEN_NAME = 'jobber'

def start():  # 410x
    if is_running():
        return {
            'state': 'already running'
        }, 0

    result = helpers.screen_start(
        JOBBER_SCREEN_NAME,
        f'mkdir -p {settings.JOBBER_SOCKET_PATH} ; /usr/lib/x86_64-linux-gnu/jobberrunner -u {settings.JOBBER_SOCKET_PATH}/cmd.sock {settings.JOBBER_CONFIG_FILE}',
        os.path.join(settings.LOGS_PATH, 'jobber.log')
    )
    if result[1] > 0:
        'jobber cannot start', 4101
    
    # wait for running
    for i in range(30):
        time.sleep(1)
        if is_running():
            return result

    return 'jobber did not start correctly after 30 seconds', 4102

def stop():  # 411x
    result = helpers.screen_stop(JOBBER_SCREEN_NAME)
    if result[1] > 0:
        return 'unexpected error', 4111, result
    return result

def get(json_format=False):  # 412x
    try:
        with open(settings.JOBBER_CONFIG_FILE, 'r') as file:
            yaml_str = file.read()
        return yaml.safe_load(yaml_str) if json_format else yaml_str, 0
    except Exception as e:
        return str(e), 4121

def set(jobber_config=None):  # 413x
    try:
        print(jobber_config)
        with open(settings.JOBBER_CONFIG_FILE, 'w') as config_file:
            config_file.write(yaml.dump(jobber_config))
        return 'success', 0
    except Exception as e:
        return str(e), 4131

def restart():  # 414x
    result = stop()
    if result[1] == 0:
        return start()
    return result

def list():  # 415x
    try:
        result = subprocess.run(['jobber', 'list'], capture_output=True, text=True)
        
        if result.returncode != 0:
            return 'jobber is not running', 4151
        else:
            lines = result.stdout.strip().split('\n')
            headers = re.split(r'\s{2,}', lines[0])
            col_positions = []
            for header in headers:
                col_positions.append(lines[0].find(header))
            jobs = []
            for line in lines[1:]:
                job = {}
                for i in range(len(headers)):
                    if i < len(headers) - 1:
                        col_length = col_positions[i+1] - col_positions[i] - 1
                    else:
                        col_length = 100
                    job[headers[i].lower().strip().replace(' ','-')] = line[col_positions[i]:col_positions[i]+col_length].strip()
                jobs.append(job)
            return {'jobs':jobs}, 0
    except Exception as e:
        return str(e), 4152

def pause(job_name=None):  # 416x
    try:
        result = subprocess.run(['jobber', 'pause', job_name], capture_output=True, text=True)
        if result.returncode != 0:
            return 'cannot pause job', 4161
        else:
            return {'result':result.stdout.strip()}, 0
    except Exception as e:
        return str(e), 4162

def resume(job_name=None):  # 417x
    try:
        result = subprocess.run(['jobber', 'resume', job_name], capture_output=True, text=True)
        if result.returncode != 0:
            return 'cannot pause job', 4171
        else:
            return {'result':result.stdout.strip()}, 0
    except Exception as e:
        return str(e), 4172

def run(job_name=None):  # 418x
    try:
        result = subprocess.run(['jobber', 'test', job_name], capture_output=True, text=True)
        if result.returncode != 0:
            return 'cannot run job', 4181
        else:
            return {'result':result.stdout.strip()}, 0
    except Exception as e:
        return str(e), 4182

def is_running():  # 419x
    return 'jobber' in helpers.screen_list()
