# api_v1.py

from flask import Flask, jsonify, request, Blueprint
import inspect

import backup
import helpers
import jobber
import player
import server
import world

api = Blueprint('api-v1', __name__, url_prefix='/api-v1')

@api.route('/get-online-server-version', methods=['GET', 'POST'])
def get_online_server_version():  # 1000
    preview = None
    if request.method == 'POST':
        try:
            preview = request.json.get('preview')
        except Exception as e:
            return _get_response(['you need a readable json-body', 1000])
    return _get_response(server.get_online_version(preview))

@api.route('/download-server', methods=['POST'])
def download_server():  # 1001
    try:
        version = request.json.get('version')
    except Exception as e:
        return _get_response(['you need a readable json-body', 1001])
    return _get_response(server.download(version))

@api.route('/get-downloaded-server-versions', methods=['GET', 'POST'])
def get_downloaded_server_versions():  # 1002
    return _get_response(server.get_downloaded_versions())

@api.route('/create-server', methods=['POST'])
def create_server():  # 1003
    try:
        properties = request.json
    except Exception as e:
        return _get_response(['you need a readable json-body', 1003])
    return _get_response(server.create(properties))

@api.route('/remove-server', methods=['POST'])
def remove_server():  # 1004
    try:
        server_name = request.json.get('server-name')
    except Exception as e:
        return _get_response(['you need a readable json-body', 1004])
    return _get_response(server.remove(server_name))

@api.route('/start-server', methods=['POST'])
def start_server():  # 1005
    try:
        properties = request.json
    except Exception as e:
        return _get_response(['you need a readable json-body', 1005])
    return _get_response(server.start(properties))

@api.route('/get-server-list', methods=['GET', 'POST'])
def get_server_list():  # 1006
    return _get_response(server.list())

@api.route('/stop-server', methods=['POST'])
def stop_server():  # 1007
    try:
        server_name = request.json.get('server-name')
    except Exception as e:
        return _get_response(['you need a readable json-body', 1007])
    try:
        wait_for_disconnected_user = helpers.is_true(request.json.get('wait-for-disconnected-user'))
    except Exception as e:
        wait_for_disconnected_user = False
    return _get_response(server.stop(server_name, wait_for_disconnected_user))

@api.route('/say-to-server', methods=['POST'])
def say_to_server():  # 1008
    try:
        server_name = request.json.get('server-name')
        message = request.json.get('message')
    except Exception as e:
        return _get_response(['you need a readable json-body', 1008])
    return _get_response(server.say_to_server(server_name, message))

@api.route('/send-command', methods=['POST'])
def send_command():  # 1009
    try:
        server_name = request.json.get('server-name')
        command = request.json.get('command')
    except Exception as e:
        return _get_response(['you need a readable json-body', 1009])
    return _get_response(server.send_command(server_name, command))

@api.route('/get-worlds', methods=['POST'])
def get_worlds():  # 1010
    try:
        server_name = request.json.get('server-name')
    except Exception as e:
        return _get_response(['you need a readable json-body', 1010])
    return _get_response(world.list(server_name))

@api.route('/create-backup', methods=['POST'])
def create_backup():  # 1011
    try:
        server_name = request.json.get('server-name')
        level_name = request.json.get('level-name')
        backup_name = request.json.get('backup-name')
        overwrite = request.json.get('overwrite')
        description = request.json.get('description')
        compress = request.json.get('compress')
    except Exception as e:
        return _get_response(['you need a readable json-body', 1011])
    return _get_response(backup.create(server_name, level_name, backup_name, overwrite, description, compress))
    
@api.route('/get-backup-list', methods=['GET', 'POST'])
def get_backup_list():  # 1012
    return _get_response(backup.list())

@api.route('/restore-backup', methods=['POST'])
def restore_backup():  # 1013
    try:
        backup_name = request.json.get('backup-name')
        server_name = request.json.get('server-name')
        level_name = request.json.get('level-name')
    except Exception as e:
        return _get_response(['you need a readable json-body', 1013])
    return _get_response(backup.restore(backup_name, server_name, level_name))

@api.route('/remove-world', methods=['POST'])
def remove_world():  # 1014
    try:
        server_name = request.json.get('server-name')
        level_name = request.json.get('level-name')
    except Exception as e:
        return _get_response(['you need a readable json-body', 1014])
    return _get_response(world.remove(server_name, level_name))

@api.route('/remove-backup', methods=['POST'])
def remove_backup():  # 1015
    try:
        backup_name = request.json.get('backup-name')
    except Exception as e:
        return _get_response(['you need a readable json-body', 1015])
    return _get_response(backup.remove(backup_name))

@api.route('/start-all-server', methods=['GET', 'POST'])
def start_all_server():  # 1016
    return _get_response(server.start_all())

@api.route('/stop-all-server', methods=['GET', 'POST'])
def stop_all_server():  # 1017
    return _get_response(server.stop_all())

@api.route('/start-server-simple', methods=['POST'])
def start_server_simple():  # 1018
    try:
        server_name = request.json.get('server-name')
    except Exception as e:
        return _get_response(['you need a readable json-body', 1018])
    return _get_response(server.start_simple(server_name))

@api.route('/get-server-details', methods=['POST'])
def get_server_details():  # 1019
    try:
        server_name = request.json.get('server-name')
    except Exception as e:
        return _get_response(['you need a readable json-body', 1019])
    return _get_response(server.details(server_name))

@api.route('/backup-all-server', methods=['GET', 'POST'])
def backup_all_server():  # 1020
    return _get_response(backup.all_server())

@api.route('/update-server', methods=['POST'])
def update_server():  # 1021
    try:
        server_name = request.json.get('server-name')
        new_version = request.json.get('version')
    except Exception as e:
        return _get_response(['you need a readable json-body', 1021])
    return _get_response(server.update(server_name, new_version))

@api.route('/update-all-server', methods=['GET', 'POST'])
def update_all_server():  # 1022
    return _get_response(server.update_all())

# JOBBER ###################################################################################
@api.route('/start-jobber', methods=['GET', 'POST'])
def start_jobber():  # 1040
    return _get_response(jobber.start())

@api.route('/stop-jobber', methods=['GET', 'POST'])
def stop_jobber():  # 1041
    return _get_response(jobber.stop())

@api.route('/get-jobber-config', methods=['POST'])
def get_jobber_config():  # 1042
    json_format = True
    try:
        json_format = request.json.get('json-format')
    except Exception as e:
        return _get_response(['you need a readable json-body', 1042])
    result = jobber.get(json_format)
    return result[0] if result[1] == 0 else _get_response(result)

@api.route('/set-jobber-config', methods=['POST'])
def set_jobber_config():  # 1043
    return _get_response(jobber.set(request.json))

@api.route('/restart-jobber', methods=['GET', 'POST'])
def restart_jobber():  # 1044
    return _get_response(jobber.restart())

@api.route('/list-jobs', methods=['GET', 'POST'])
def list_jobs():  # 1045
    return _get_response(jobber.list())

@api.route('/pause-job', methods=['POST'])
def pause_job():  # 1046
    try:
        job_name = request.json.get('job-name')
    except Exception as e:
        return _get_response(['you need a readable json-body', 1046])
    return _get_response(jobber.pause(job_name))

@api.route('/resume-job', methods=['POST'])
def resume_job():  # 1047
    try:
        job_name = request.json.get('job-name')
    except Exception as e:
        return _get_response(['you need a readable json-body', 1047])
    return _get_response(jobber.resume(job_name))

@api.route('/run-job', methods=['POST'])
def run_job():  # 1048
    try:
        job_name = request.json.get('job-name')
    except Exception as e:
        return _get_response(['you need a readable json-body', 1048])
    return _get_response(jobber.run(job_name))

# PLAYER ###################################################################################

@api.route('/get-known-players', methods=['GET', 'POST'])
def get_known_players():  # 1050
    return _get_response(player.get_known())

@api.route('/add-player', methods=['POST'])
def add_player():  # 1051
    try:
        player_name = request.json.get('player-name')
        xuid = request.json.get('xuid')
    except Exception as e:
        return _get_response(['you need a readable json-body', 1051])
    return _get_response(player.add(player_name, xuid))

@api.route('/update-permission', methods=['POST'])
def update_permission():  # 1052
    try:
        server_name = request.json.get('server-name')
        name = request.json.get('player-name')
        permission = request.json.get('permission')
    except Exception as e:
        return _get_response(['you need a readable json-body', 1052])
    return _get_response(player.update_permission(server_name, name, permission))

# OTHER ####################################################################################

def _get_response(result):
    if result[1] == 0:
        return jsonify({
            'function': inspect.stack()[1].function,
            'result': result[0]
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

