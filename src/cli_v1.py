# cli_v1.py

import click
import backup
import server
import sys

@click.group()
def cli():
    pass

@cli.command()
@click.option('--preview', is_flag=True, help='Get preview-version of bedrock-server')
def get_online_server_version(preview):  # 1050
    try:
        _get_output(server.get_online_version(preview))
    except Exception as e:
        _get_output([str(e), 1050])

@cli.command()
@click.option('--server-version', '-v', prompt=True, help='Version of the server')
def download_server(server_version):  # 1051
    try:
        _get_output(server.download(server_version))
    except Exception as e:
        _get_output([str(e), 1051])

@cli.command()
def get_downloaded_server_versions():  # 1052
    try:
        _get_output(server.get_downloaded_versions())
    except Exception as e:
        _get_output([str(e), 1052])

@cli.command()
@click.option('--property', '-p', multiple=True, nargs=2, help='Server properties in the format key=value')
def create_server(property):  # 1053
    try:
        properties = dict(property)
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
@click.option('--property', '-p', multiple=True, nargs=2, help='Server properties in the format key=value')
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
@click.option('--level-name', '-l', prompt=True, help='Name of the world')
@click.option('--reason', '-r', help='Reason for the backup')
@click.option('--description', '-d', help='Description for the backup')
@click.option('--compress', '-c', is_flag=True, help='Will compress the backup files')
def create_backup(server_name, level_name, reason, description, compress):  # 1061
    try:
        _get_output(backup.create(server_name, level_name, reason, description, compress))
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
        _get_output(server.remove_world(server_name, level_name))
    except Exception as e:
        _get_output([str(e), 1064])

@cli.command()
@click.option('--backup-name', '-b', prompt=True, help='Name of the backup')
def remove_backup(backup_name):  # 1065
    try:
        _get_output(backup.remove(backup_name))
    except Exception as e:
        _get_output([str(e), 1065])


def _get_output(result):
    if result[1] == 0:
        click.echo(result[0], file=sys.stdout)
        return 0

    def _build_err_stack(err_result):
        r = f"message: {err_result[0]}, code: {err_result[1]}"
        if len(err_result) == 3:
            r += "\n" + _build_err_stack(err_result[2])
        return r

    click.echo(f"Error: {_build_err_stack(result)}", file=sys.stderr)
    return 1

if __name__ == '__main__':
    cli()