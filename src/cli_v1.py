# cli_v1.py
# err:10xx

import click
import json
import sys

import backup
import jobber
import player
import server
import world

ctx = {}

@click.group()
@click.option('--formatted/--no-formatted', default=True, help='Enable verbose mode for all commands')
def cli(formatted):
    ctx['formatted'] = formatted

@cli.command()
@click.option('--preview', is_flag=True, help='Get preview-version of bedrock-server')
def get_online_server_version(preview):  # 1050
    try:
        _get_output(server.get_online_version(preview))
    except Exception as e:
        _get_output([str(e), 1050])

@cli.command()
@click.option('--version', '-v', help='Version of the server')
def download_server(version):  # 1051
    try:
        _get_output(server.download(version))
    except Exception as e:
        _get_output([str(e), 1051])

@cli.command()
def get_downloaded_server_versions():  # 1052
    try:
        _get_output(server.get_downloaded_versions())
    except Exception as e:
        _get_output([str(e), 1052])

@cli.command()
@click.option('--server-name', '-n', prompt=True, help='Name of the server')
@click.option('--version', '-v', default=None, help='Server-version. default highest')
@click.option('--property', '-p', multiple=True, nargs=2, help='Server properties in the format: key value')
def create_server(server_name, version, property):  # 1053
    try:
        properties = dict(property)
        properties['server-name'] = server_name
        if version != None:
            properties['version'] = version
        _get_output(server.create(properties))
    except Exception as e:
        _get_output([str(e), 1053])

@cli.command()
@click.option('--server-name', '-n', prompt=True, help='Name of the server')
def remove_server(server_name):  # 1054
    try:
        _get_output(server.remove(server_name))
    except Exception as e:
        _get_output([str(e), 1054])
    
@cli.command()
@click.option('--server-name', '-n', prompt=True, help='Name of the server')
@click.option('--property', '-p', multiple=True, nargs=2, help='Server properties in the format: key value')
def start_server(server_name, property):  # 1055
    try:
        properties = dict(property)
        properties['server-name'] = server_name
        _get_output(server.start(properties))
    except Exception as e:
        _get_output([str(e), 1055])

@cli.command()
def get_server_list():  # 1056
    try:
        _get_output(server.list())
    except Exception as e:
        _get_output([str(e), 1056])

@cli.command()
@click.option('--server-name', '-n', prompt=True, help='Name of the server')
@click.option('--wait-for-disconnected-user', is_flag=True, help='Wait for disconnected user')
def stop_server(server_name, wait_for_disconnected_user):  # 1057
    try:
        _get_output(server.stop(server_name, wait_for_disconnected_user))
    except Exception as e:
        _get_output([str(e), 1057])

@cli.command()
@click.option('--server-name', '-n', prompt=True, help='Name of the server')
@click.option('--message', '-m', prompt=True, help='Your message for the server')
def say_to_server(server_name, message):  # 1058
    try:
        _get_output(server.say_to_server(server_name, message))
    except Exception as e:
        _get_output([str(e), 1058])

@cli.command()
@click.option('--server-name', '-n', prompt=True, help='Name of the server')
@click.option('--command', '-c', prompt=True, help='Minecraft command for the server')
def send_command(server_name, command):  # 1059
    try:
        _get_output(server.send_command(server_name, command))
    except Exception as e:
        _get_output([str(e), 1059])

@cli.command()
@click.option('--server-name', '-n', prompt=True, help='Name of the server')
def get_worlds(server_name):  # 1060
    try:
        _get_output(server.get_worlds(server_name))
    except Exception as e:
        _get_output([str(e), 1060])

@cli.command()
@click.option('--server-name', '-n', prompt=True, help='Name of the server')
@click.option('--level-name', '-l', help='Name of the world')
@click.option('--backup_name', '-b', help='Name for this backup')
@click.option('--overwrite', '-o', is_flag=True, help='Will overwrite exists backup-file')
@click.option('--description', '-d', help='Description for the backup')
@click.option('--compress', '-c', is_flag=True, help='Will compress the backup-files')
def create_backup(server_name, level_name, backup_name, overwrite, description, compress):  # 1061
    try:
        _get_output(backup.create(server_name, level_name, backup_name, overwrite, description, compress))
    except Exception as e:
        _get_output([str(e), 1061])
    
@cli.command()
def get_backup_list():  # 1062
    try:
        _get_output(backup.list())
    except Exception as e:
        _get_output([str(e), 1062])

@cli.command()
@click.option('--backup-name', '-b', prompt=True, help='Name of the backup')
@click.option('--server-name', '-n', prompt=True, help='Name of the server')
@click.option('--level-name', '-l', prompt=True, help='Name of the world')
def restore_backup(backup_name, server_name, level_name):  # 1063
    try:
        _get_output(backup.restore(backup_name, server_name, level_name))
    except Exception as e:
        _get_output([str(e), 1063])

@cli.command()
@click.option('--server-name', '-n', prompt=True, help='Name of the server')
@click.option('--level-name', '-l', prompt=True, help='Name of the world')
def remove_world(server_name, level_name):  # 1064
    try:
        _get_output(world.remove(server_name, level_name))
    except Exception as e:
        _get_output([str(e), 1064])

@cli.command()
@click.option('--backup-name', '-b', prompt=True, help='Name of the backup')
def remove_backup(backup_name):  # 1065
    try:
        _get_output(backup.remove(backup_name))
    except Exception as e:
        _get_output([str(e), 1065])

@cli.command()
def start_all_server():  # 1066
    try:
        _get_output(server.start_all())
    except Exception as e:
        _get_output([str(e), 1066])

@cli.command()
def stop_all_server():  # 1067
    try:
        _get_output(server.stop_all())
    except Exception as e:
        _get_output([str(e), 1067])

@cli.command()
@click.option('--server-name', '-n', prompt=True, help='Name of the server')
def start_server_simple(server_name):  # 1068
    try:
        _get_output(server.start_simple(server_name))
    except Exception as e:
        _get_output([str(e), 1068])

@cli.command()
@click.option('--server-name', '-n', prompt=True, help='Name of the server')
def get_server_details(server_name):  # 1069
    try:
        _get_output(server.details(server_name))
    except Exception as e:
        _get_output([str(e), 1069])

@cli.command()
def backup_all_server():  # 1070
    try:
        _get_output(backup.all_server())
    except Exception as e:
        _get_output([str(e), 1070])

@cli.command()
@click.option('--server-name', '-n', prompt=True, help='Name of the server')
@click.option('--version', '-v', default=None, help='Server-version. default highest')
@click.option('--force', is_flag=True, help='Forces the installation of an older version.')
def update_server(server_name, version, force):  # 1071
    try:
        _get_output(server.update(server_name, version, force))
    except Exception as e:
        _get_output([str(e), 1071])

@cli.command()
def update_all_server():  # 1072
    try:
        _get_output(server.update_all())
    except Exception as e:
        _get_output([str(e), 1072])

# JOBBER ###################################################################################
@cli.command()
def start_jobber():  # 1100
    try:
        _get_output(jobber.start())
    except Exception as e:
        _get_output([str(e), 1100])

@cli.command()
def stop_jobber():  # 1101
    try:
        _get_output(jobber.stop())
    except Exception as e:
        _get_output([str(e), 1101])

@cli.command()
@click.option('--json-format', '-j', is_flag=True, help='Will output jobber-config as json')
def get_jobber_config(json_format):  # 1102
    try:
        _get_output(jobber.get(json_format))
    except Exception as e:
        _get_output([str(e), 1102])

#@cli.command()
#@click.option('--config', '-c', prompt=True, help='Name of the job')
#def set_jobber_config(jobber_config):  # 1103
#    try:
#        _get_output(jobber.set(jobber_config))
#    except Exception as e:
#        _get_output([str(e), 1103])

@cli.command()
def restart_jobber():  # 1104
    try:
        _get_output(jobber.restart())
    except Exception as e:
        _get_output([str(e), 1104])

@cli.command()
def list_jobs():  # 1105
    try:
        _get_output(jobber.list())
    except Exception as e:
        _get_output([str(e), 1105])

@cli.command()
@click.option('--job-name', '-n', prompt=True, help='Name of the job')
def pause_job(job_name):  # 1106
    try:
        _get_output(jobber.pause(job_name))
    except Exception as e:
        _get_output([str(e), 1106])

@cli.command()
@click.option('--job-name', '-n', prompt=True, help='Name of the job')
def resume_job(job_name):  # 1107
    try:
        _get_output(jobber.resume(job_name))
    except Exception as e:
        _get_output([str(e), 1107])

@cli.command()
@click.option('--job-name', '-n', prompt=True, help='Name of the job')
def run_job(job_name):  # 1108
    try:
        _get_output(jobber.run(job_name))
    except Exception as e:
        _get_output([str(e), 1108])

# PLAYER ###################################################################################

@cli.command()
def get_known_players():  # 1110
    try:
        _get_output(player.get_known())
    except Exception as e:
        _get_output([str(e), 1110])

@cli.command()
@click.option('--player-name', '-u', prompt=True, help='Player-Name')
@click.option('--xuid', '-x', prompt=True, help='XUID')
def add_player(player_name, xuid):  # 1111
    try:
        _get_output(player.add(player_name, xuid))
    except Exception as e:
        _get_output([str(e), 1111])

@cli.command()
@click.option('--server-name', '-n', prompt=True, help='Name of the server')
@click.option('--player-name', '-u', prompt=True, help='Player-Name')
@click.option('--permission', '-p', help='Allowed values: "visitor", "member", "operator" or empty to remove permission')
def update_permission(server_name, player_name, permission):  # 1112
    try:
        _get_output(player.update_permission(server_name, player_name, permission))
    except Exception as e:
        _get_output([str(e), 1112])

@cli.command()
@click.option('--server-name', '-n', prompt=True, help='Name of the server')
@click.option('--player-name', '-u', prompt=True, help='Player-Name')
@click.option('--remove', '-r', is_flag=True, help='Remove an existing player')
def update_allowlist(server_name, player_name, remove):  # 1113
    try:
        _get_output(player.update_allowlist(server_name, player_name, remove))
    except Exception as e:
        _get_output([str(e), 1113])

# OTHER ####################################################################################

def _get_output(result):
    def _get_json(json_str):
        try:
            return json.dumps(json_str if isinstance(json_str, dict) else json.loads(json_str), indent=2)
        except ValueError:
            return False
        
    if result[1] == 0:
        output = _get_json(result[0]) if ctx['formatted'] else result[0]
        click.echo(output if output != False else result[0], file=sys.stdout)
        return 0

    def _build_err_stack(err_result):
        r = f"message: {err_result[0]}, code: {err_result[1]}"
        if len(err_result) == 3:
            r += "\n" + _build_err_stack(err_result[2])
        return r

    click.echo(f"Error:\n{_build_err_stack(result)}", file=sys.stderr)
    return 1

if __name__ == '__main__':
    cli()
