# api_v1.py

from flask import Flask, jsonify, request, Blueprint

import backup
import inspect
import helpers
import server

api = Blueprint('api-v1', __name__, url_prefix='/api-v1')

@api.route('/get_online_server_version', methods=['GET', 'POST'])  # 1010
def get_online_server_version():
    preview = None
    if request.method == 'POST':
        try:
            preview = request.json.get('preview')
        except Exception as e:
            return _get_response(['you need a readable json-body', 1010])

    return _get_response(server.get_online_version(preview))

@api.route('/download_server', methods=['POST'])  # 1011
def download_server():
    try:
        version = request.json.get('server-version')
    except Exception as e:
        return _get_response(['you need a readable json-body', 1011])

    return _get_response(server.download(version))

@api.route('/get_downloaded_server_versions', methods=['GET', 'POST'])
def get_downloaded_server_versions():
    return _get_response(server.get_downloaded_versions())

@api.route('/create_server', methods=['POST'])  # 1012
def create_server():
    try:
        properties = request.json
    except Exception as e:
        return _get_response(['you need a readable json-body', 1012])
        
    return _get_response(server.create(properties))

@api.route('/remove_server', methods=['POST'])  # 1013
def remove_server():
    try:
        server_name = request.json.get('server-name')
    except Exception as e:
        return _get_response(['you need a readable json-body', 1013])
        
    return _get_response(server.remove(server_name))

@api.route('/start_server', methods=['POST'])  # 1014
def start_server():
    try:
        properties = request.json
    except Exception as e:
        return _get_response(['you need a readable json-body', 1014])
        
    return _get_response(server.start(properties))

@api.route('/get_server_list', methods=['GET', 'POST'])
def get_server_list():
    return _get_response(server.list())

@api.route('/stop_server', methods=['POST'])  # 1015
def stop_server():
    try:
        server_name = request.json.get('server-name')
    except Exception as e:
        return _get_response(['you need a readable json-body', 1015])
        
    try:
        wait_for_disconnected_user = helpers._is_true(request.json.get('wait-for-disconnected-user'))
    except Exception as e:
        wait_for_disconnected_user = False
        
    return _get_response(server.stop(server_name, wait_for_disconnected_user))

@api.route('/say_to_server', methods=['POST'])  # 1016
def say_to_server():
    try:
        server_name = request.json.get('server-name')
        message = request.json.get('message')
    except Exception as e:
        return _get_response(['you need a readable json-body', 1016])
        
    return _get_response(server.say_to_server(server_name, message))

@api.route('/send_command', methods=['POST'])  # 1017
def send_command():
    try:
        server_name = request.json.get('server-name')
        command = request.json.get('command')
    except Exception as e:
        return _get_response(['you need a readable json-body', 1017])
        
    return _get_response(server.send_command(server_name, command))

@api.route('/get_worlds', methods=['POST'])  # 1018
def get_worlds():
    try:
        server_name = request.json.get('server-name')
    except Exception as e:
        return _get_response(['you need a readable json-body', 1018])
        
    return _get_response(server.get_worlds(server_name))

@api.route('/create_backup', methods=['POST'])  # 1019
def create_backup():
    try:
        server_name = request.json.get('server-name')
        level_name = request.json.get('level-name')
        reason = request.json.get('reason')
        description = request.json.get('description')
    except Exception as e:
        return _get_response(['you need a readable json-body', 1019])
        
    return _get_response(backup.create(server_name, level_name, reason, description))
    
@api.route('/get_backup_list', methods=['GET', 'POST'])
def get_backup_list():
    return _get_response(backup.list())

@api.route('/restore_backup', methods=['POST'])  # 1020
def restore_backup():
    try:
        backup_name = request.json.get('backup-name')
        server_name = request.json.get('server-name')
        level_name = request.json.get('level-name')
    except Exception as e:
        return _get_response(['you need a readable json-body', 1020])
        
    return _get_response(backup.restore(backup_name, server_name, level_name))

@api.route('/remove_world', methods=['POST'])  # 1021
def remove_world():
    try:
        server_name = request.json.get('server-name')
        level_name = request.json.get('level-name')
    except Exception as e:
        return _get_response(['you need a readable json-body', 1021])
        
    return _get_response(server.remove_world(server_name, level_name))

@api.route('/remove_backup', methods=['POST'])  # 1022
def remove_backup():
    try:
        backup_name = request.json.get('backup-name')
    except Exception as e:
        return _get_response(['you need a readable json-body', 1022])
        
    return _get_response(backup.remove(backup_name))

def _get_response(result):
    if result[1] == 0:
        return jsonify({
            'result': {
                f'{inspect.stack()[1].function}': result[0]
            },
            'function': inspect.stack()[1].function
        }), 200

    def _build_err_stack(err_result):
        r = {
            'message': err_result[0],
            'code': err_result[1]
        }
        if len(err_result) == 3:
            r['stack'] = _build_err_stack(err_result[2])
        return r

    return jsonify({
            'function': inspect.stack()[1].function,
            'error': _build_err_stack(result)
        }), 400

