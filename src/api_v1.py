from flask import Flask, jsonify, request, Blueprint

import inspect
import helpers
import server

api = Blueprint('api-v1', __name__, url_prefix='/api-v1')

@api.route('/get_latest_server_version')
def get_latest_server_version():
    return _get_response(server.get_local_version('latest'))

@api.route('/get_downloaded_server_version')
def get_downloaded_server_version():
    return _get_response(server.get_local_version('downloaded'))

@api.route('/get_online_server_version')
def get_online_server_version():
    return _get_response(server.get_online_version())

@api.route('/download_server', methods=['POST'])  # 1011
def download_server():
    try:
        version = request.json.get('version')
    except Exception as e:
        version = None
    
    if not version:
        result = server.get_local_version('downloaded')
        if result[1] == 0:
            version = result[0]
        else:
            result = server.get_online_version()
            if result[1] == 0:
                version = result[0]
            else:
                return _get_response(['cannot get local- and online-version', 1011, result])

    return _get_response(server.download(version))

@api.route('/create_server', methods=['POST'])  # 1012
def create_server():
    try:
        properties = request.json
    except Exception as e:
        return _get_response(['you need an json-body', 1012])
        
    return _get_response(server.create(properties))

@api.route('/remove_server', methods=['POST'])  # 1013
def remove_server():
    try:
        server_name = request.json.get('server-name')
    except Exception as e:
        return _get_response(['you need an json-body', 1013])
        
    return _get_response(server.remove(server_name))

@api.route('/start_server', methods=['POST'])  # 1014
def start_server():
    try:
        server_name = request.json.get('server-name')
        server_port = request.json.get('server-port')
    except Exception as e:
        return _get_response(['you need an json-body', 1014])
        
    return _get_response(server.start(server_name, server_port))

@api.route('/get_server_list')
def get_server_list():
    return _get_response(server.list())

@api.route('/stop_server', methods=['POST'])  # 1015
def stop_server():
    try:
        server_name = request.json.get('server-name')
    except Exception as e:
        return _get_response(['you need an json-body', 1015])
        
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
        return _get_response(['you need an json-body', 1016])
        
    return _get_response(server.say_to_server(server_name, message))

@api.route('/send_command', methods=['POST'])  # 1017
def send_command():
    try:
        server_name = request.json.get('server-name')
        command = request.json.get('command')
    except Exception as e:
        return _get_response(['you need an json-body', 1017])
        
    return _get_response(server.send_command(server_name, command))

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

