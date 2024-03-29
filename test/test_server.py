# test_server.py

"""
pip install pytest;
pytest -s ../test
"""

import sys
import os
import pytest
import re

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../app')))

import settings
import helpers
import server
import backup
import world

rnd = '_' + helpers.rnd(3)
ctx = {}

@pytest.fixture(scope='session', autouse=True)
def prepare():
    settings.DOWNLOADED_PATH += rnd
    settings.SERVER_PATH += rnd
    settings.LOGS_PATH += rnd
    settings.BACKUPS_PATH += rnd
    settings.INCREMENTAL_PATH += rnd
    
    os.mkdir(settings.DOWNLOADED_PATH)
    os.chmod(settings.DOWNLOADED_PATH, 0o777)
    os.mkdir(settings.SERVER_PATH)
    os.chmod(settings.SERVER_PATH, 0o777)
    os.mkdir(settings.LOGS_PATH)
    os.chmod(settings.LOGS_PATH, 0o777)
    os.mkdir(settings.BACKUPS_PATH)
    os.chmod(settings.BACKUPS_PATH, 0o777)
    os.mkdir(settings.INCREMENTAL_PATH)
    os.chmod(settings.INCREMENTAL_PATH, 0o777)

    yield True
    server.stop_all()
    helpers.remove_dirtree(settings.DOWNLOADED_PATH)
    helpers.remove_dirtree(settings.SERVER_PATH)
    helpers.remove_dirtree(settings.LOGS_PATH)
    helpers.remove_dirtree(settings.BACKUPS_PATH)
    helpers.remove_dirtree(settings.INCREMENTAL_PATH)

def test_get_online_stable_version():
    result = server.get_online_version()
    assert isinstance(result, tuple)
    assert result[1] == 0
    assert isinstance(result[0], dict)
    assert "branch" in result[0]
    assert "version" in result[0]
    assert result[0]["branch"] == "stable"
    assert isinstance(result[0]["version"], str)
    assert len(re.search(r'([0-9\.]+)', result[0]["version"]).groups()) == 1

    assert result == server.get_online_version(False)
    assert result == server.get_online_version(None)
    assert result == server.get_online_version('FALSE')
    assert result == server.get_online_version('off')
    assert result == server.get_online_version('no')
    assert result == server.get_online_version(0)
    ctx['stable-version'] = result[0]["version"]

def test_get_online_preview_version():
    result = server.get_online_version(True)
    assert isinstance(result, tuple)
    assert result[1] == 0
    assert isinstance(result[0], dict)
    assert "branch" in result[0]
    assert "version" in result[0]
    assert result[0]["branch"] == "preview"
    assert isinstance(result[0]["version"], str)
    assert len(re.search(r'([0-9\.]+)', result[0]["version"]).groups()) == 1

    assert result == server.get_online_version('TRUE')
    assert result == server.get_online_version('on')
    assert result == server.get_online_version('yes')
    assert result == server.get_online_version(1)
    ctx['preview-version'] = result[0]["version"]

def test_get_downloaded_versions_empty():
    result = server.get_downloaded_versions()
    assert isinstance(result, tuple)
    assert result[1] == 0
    assert isinstance(result[0], dict)
    assert "versions" in result[0]
    assert isinstance(result[0]["versions"], list)
    assert "count" in result[0]
    assert isinstance(result[0]["count"], int)
    assert len(result[0]["versions"]) == result[0]["count"]
    assert result[0]["count"] == 0

def test_create_server_fail_empty():
    result = server.create()
    assert isinstance(result, tuple)
    assert result[1] == 1131  # parameter must be a object
    result = server.create({})
    assert isinstance(result, tuple)
    assert result[1] == 1132  # server-name is required
    result = server.create({'server-name':''})
    assert isinstance(result, tuple)
    assert result[1] == 1132  # server-name is empty
    result = server.create({'server-name':'blubb'})
    assert isinstance(result, tuple)
    assert result[1] == 1133  # download binaries first

def test_download_server_stable_version(first_result=None):
    result = server.download()
    assert isinstance(result, tuple)
    assert result[1] == 0
    assert isinstance(result[0], dict)
    assert "version" in result[0]
    assert isinstance(result[0]["version"], str)
    assert len(re.search(r'([0-9\.]+)', result[0]["version"]).groups()) == 1
    assert result[0]["version"] == ctx['stable-version']
    assert "state" in result[0]
    assert isinstance(result[0]["state"], str)
    if result[0]["state"] == "downloaded":
        assert "branch" in result[0]
        assert result[0]["branch"] == "stable"
        assert first_result == None
        test_download_server_stable_version(result)
    elif result[0]["state"] == "already downloaded" or result[0]["state"] == "already exists":
        assert result == server.download(None)
        assert result == server.download('')
        assert result == server.download(ctx['stable-version'])

def test_get_downloaded_versions_filled_1():
    result = server.get_downloaded_versions()
    assert isinstance(result, tuple)
    assert result[1] == 0
    assert isinstance(result[0], dict)
    assert "versions" in result[0]
    assert isinstance(result[0]["versions"], list)
    assert "count" in result[0]
    assert isinstance(result[0]["count"], int)
    assert len(result[0]["versions"]) == result[0]["count"]
    assert result[0]["count"] == 1
    assert ctx['stable-version'] in result[0]["versions"]

def test_download_server_preview_version(first_result=None):
    result = server.download(ctx['preview-version'])
    assert isinstance(result, tuple)
    assert result[1] == 0
    assert isinstance(result[0], dict)
    assert "version" in result[0]
    assert isinstance(result[0]["version"], str)
    assert len(re.search(r'([0-9\.]+)', result[0]["version"]).groups()) == 1
    assert result[0]["version"] == ctx['preview-version']
    assert "state" in result[0]
    assert isinstance(result[0]["state"], str)
    if result[0]["state"] == "downloaded":
        assert "branch" in result[0]
        assert result[0]["branch"] == "preview"
        assert first_result == None
        test_download_server_preview_version(result)
    elif result[0]["state"] == "already downloaded" or result[0]["state"] == "already exists":
        assert result == server.download(ctx['preview-version'])

def test_download_server_fail():
    result = server.download('blubb')
    assert isinstance(result, tuple)
    assert result[1] == 1112  # cannot download version

def test_get_downloaded_versions_filled_2():
    result = server.get_downloaded_versions()
    assert isinstance(result, tuple)
    assert result[1] == 0
    assert isinstance(result[0], dict)
    assert "versions" in result[0]
    assert isinstance(result[0]["versions"], list)
    assert "count" in result[0]
    assert isinstance(result[0]["count"], int)
    assert len(result[0]["versions"]) == result[0]["count"]
    assert result[0]["count"] == 2
    assert ctx['stable-version'] in result[0]["versions"]
    assert ctx['preview-version'] in result[0]["versions"]

def test_get_server_list_empty():
    result = server.list()
    assert isinstance(result, tuple)
    assert result[1] == 0
    assert isinstance(result[0], dict)
    assert "created-server" in result[0]
    assert isinstance(result[0]["created-server"], list)
    assert len(result[0]["created-server"]) == 0
    assert "running-server" in result[0]
    assert isinstance(result[0]["running-server"], list)
    assert len(result[0]["running-server"]) == 0

def test_create_server():
    result = server.create({'server-name':'test-server-1', 'version':'1.1.1.1'})
    assert isinstance(result, tuple)
    assert result[1] == 1134  # version does not exists
    
    result = server.create({'server-name':'test-server-1', 'level-name':'level-1'})
    assert isinstance(result, tuple)
    assert result[1] == 0
    assert isinstance(result[0], dict)
    assert len(result[0]) == 4
    assert "server-name" in result[0]
    assert isinstance(result[0]["server-name"], str)
    assert result[0]["server-name"] == 'test-server-1'
    assert 'version' in result[0]
    assert result[0]["version"] == ctx["preview-version"]
    assert 'branch' in result[0]
    assert result[0]["branch"] == "preview"
    assert "default-properties" in result[0]
    assert isinstance(result[0]["default-properties"], dict)
    assert len(result[0]["default-properties"]) == 2
    assert 'server-name' in result[0]["default-properties"]
    assert result[0]["default-properties"]["server-name"] == 'test-server-1'
    assert 'level-name' in result[0]["default-properties"]
    assert result[0]["default-properties"]["level-name"] == 'level-1'

    result = server.create({'server-name':'test-server-1'})
    assert isinstance(result, tuple)
    assert result[1] == 1135  # server already exists

def test_get_server_list_created():
    result = server.list()
    assert isinstance(result, tuple)
    assert result[1] == 0
    assert isinstance(result[0], dict)
    assert len(result[0]) == 2
    assert "created-server" in result[0]
    assert isinstance(result[0]["created-server"], list)
    assert len(result[0]["created-server"]) == 1
    assert 'test-server-1' in result[0]["created-server"]
    assert "running-server" in result[0]
    assert isinstance(result[0]["running-server"], list)
    assert len(result[0]["running-server"]) == 0

def test_start_server():
    result = server.start()
    assert isinstance(result, tuple)
    assert result[1] == 1151  # parameter must be a object

    result = server.start({})
    assert isinstance(result, tuple)
    assert result[1] == 1152  # server-name is required

    result = server.start({'server-name':'blubb'})
    assert isinstance(result, tuple)
    assert result[1] == 1153  # server not exists

    result = server.start({'server-name':'test-server-1','server-port':19111})
    assert isinstance(result, tuple)
    assert result[1] == 0
    assert len(result[0]) == 6
    assert "server-name" in result[0]
    assert isinstance(result[0]["server-name"], str)
    assert result[0]["server-name"] == 'test-server-1'
    assert "version" in result[0]
    assert isinstance(result[0]["version"], str)
    assert result[0]["version"] == ctx["preview-version"]
    assert 'branch' in result[0]
    assert result[0]["branch"] == "preview"
    assert "state" in result[0]
    assert isinstance(result[0]["state"], str)
    assert result[0]["state"] == 'started'
    assert "times" in result[0]
    assert isinstance(result[0]["times"], int)
    assert "log" in result[0]
    assert isinstance(result[0]["log"], dict)

def test_get_server_list_running():
    result = server.list()
    assert isinstance(result, tuple)
    assert result[1] == 0
    assert isinstance(result[0], dict)
    assert len(result[0]) == 2
    assert "created-server" in result[0]
    assert isinstance(result[0]["created-server"], list)
    assert len(result[0]["created-server"]) == 1
    assert 'test-server-1' in result[0]["created-server"]
    assert "running-server" in result[0]
    assert isinstance(result[0]["running-server"], list)
    assert 'test-server-1' in result[0]["running-server"]
    assert len(result[0]["running-server"]) == 1

def test_stop_server():
    result = server.stop()
    assert isinstance(result, tuple)
    assert result[1] == 1161  # server-name is required

    result = server.stop('blubb')
    assert isinstance(result, tuple)
    assert result[1] == 0
    assert 'server-name' in result[0]
    assert result[0]['server-name'] == 'blubb'
    assert 'state' in result[0]
    assert result[0]['state'] == 'nothing to stop'

    result = server.stop('test-server-1')
    assert isinstance(result, tuple)
    assert result[1] == 0
    assert 'server-name' in result[0]
    assert result[0]['server-name'] == 'test-server-1'
    assert 'state' in result[0]
    assert result[0]['state'] == 'stopped'

    result = server.stop('test-server-1')
    assert isinstance(result, tuple)
    assert result[1] == 0
    assert 'server-name' in result[0]
    assert result[0]['server-name'] == 'test-server-1'
    assert 'state' in result[0]
    assert result[0]['state'] == 'nothing to stop'

def test_start_simple_server():
    result = server.start_simple()
    assert isinstance(result, tuple)
    assert result[1] == 1241  # server-name is required

    result = server.start_simple('blubb')
    assert isinstance(result, tuple)
    assert result[1] == 1242  # server not exists

    result = server.start_simple('test-server-1')
    assert isinstance(result, tuple)
    assert result[1] == 0
    assert 'server-name' in result[0]
    assert result[0]['server-name'] == 'test-server-1'
    assert 'state' in result[0]
    assert result[0]['state'] == 'started'

    result = server.start_simple('test-server-1')
    assert isinstance(result, tuple)
    assert result[1] == 0
    assert 'server-name' in result[0]
    assert result[0]['server-name'] == 'test-server-1'
    assert 'state' in result[0]
    assert result[0]['state'] == 'already running'

def test_remove_server_fail():
    result = server.remove()
    assert isinstance(result, tuple)
    assert result[1] == 1141  # server-name is required

    result = server.remove('blubb')
    assert isinstance(result, tuple)
    assert result[1] == 1142  # server not exists

    result = server.remove('test-server-1')
    assert isinstance(result, tuple)
    assert result[1] == 1143  # server is running

def test_say_to_server():
    result = server.say_to_server()
    assert isinstance(result, tuple)
    assert result[1] == 1171  # server-name is required

    result = server.say_to_server('blubb')
    assert isinstance(result, tuple)
    assert result[1] == 1172  # server not running

    result = server.say_to_server('test-server-1')
    assert isinstance(result, tuple)
    assert result[1] == 1173  # message is required

    result = server.say_to_server('test-server-1', 'test')
    assert isinstance(result, tuple)
    assert result[1] == 0
    assert 'server-name' in result[0]
    assert result[0]['server-name'] == 'test-server-1'
    assert 'message' in result[0]
    assert result[0]['message'] == 'test'

def test_send_command():
    result = server.send_command()
    assert isinstance(result, tuple)
    assert result[1] == 1181  # server-name is required

    result = server.send_command('blubb')
    assert isinstance(result, tuple)
    assert result[1] == 1182  # server not running

    result = server.send_command('test-server-1')
    assert isinstance(result, tuple)
    assert result[1] == 1183  # command is required

    result = server.send_command('test-server-1', 'gamerule showcoordinates true')
    assert isinstance(result, tuple)
    assert result[1] == 0
    assert 'server-name' in result[0]
    assert result[0]['server-name'] == 'test-server-1'
    assert 'command' in result[0]
    assert result[0]['command'] == 'gamerule showcoordinates true'

def test_parse_log():
    result = server.parse_log()
    assert isinstance(result, tuple)
    assert result[1] == 1201  # server-name is required

    result = server.parse_log('blubb')
    assert isinstance(result, tuple)
    assert result[1] == 1202  # server not exists

    result = server.parse_log('test-server-1')
    assert isinstance(result, tuple)
    assert result[1] == 0
    assert 'server-name' in result[0]
    assert result[0]['server-name'] == 'test-server-1'
    assert 'start-time' in result[0]
    assert 'started-time' in result[0]
    assert 'level-name' in result[0]
    assert 'gamemode' in result[0]
    assert 'difficulty' in result[0]
    assert 'state' in result[0]
    assert 'stop-time' not in result[0]

def test_get_worlds():
    result = world.list()
    assert isinstance(result, tuple)
    assert result[1] == 3011  # server-name is required

    result = world.list('blubb')
    assert isinstance(result, tuple)
    assert result[1] == 3012  # server not exists

    result = world.list('test-server-1')
    assert isinstance(result, tuple)
    assert result[1] == 0
    assert 'server-name' in result[0]
    assert result[0]['server-name'] == 'test-server-1'
    assert 'worlds' in result[0]
    assert len(result[0]['worlds']) == 1
    assert 'level-1' in result[0]['worlds']

def test_stop_all_server():
    result = server.stop_all()
    assert isinstance(result, tuple)
    assert result[1] == 0
    assert isinstance(result[0], dict)
    assert len(result[0]) == 3
    assert "stopped" in result[0]
    assert isinstance(result[0]["stopped"], list)
    assert 'test-server-1' in result[0]["stopped"]
    assert "already stopped" in result[0]
    assert isinstance(result[0]["already stopped"], list)
    assert "failed" in result[0]
    assert isinstance(result[0]["failed"], list)
    
    result = server.stop_all()
    assert isinstance(result, tuple)
    assert result[1] == 0
    assert 'test-server-1' in result[0]["already stopped"]

def test_create_server_2():
    result = server.create({'server-name':'test-server-2', 'server-port':19111, 'server-portv6':'::', 'version': ctx["stable-version"]})
    assert isinstance(result, tuple)
    assert result[1] == 0

def test_get_current_world_fail():
    result = world.get_current_world()
    assert isinstance(result, tuple)
    assert result[1] == 3021  # server-name is required

    result = world.get_current_world('blubb')
    assert isinstance(result, tuple)
    assert result[1] == 3022  # server not exists

    result = world.get_current_world('test-server-2')
    assert isinstance(result, tuple)
    assert result[1] == 3023  # server is never started

def test_start_all_server():
    result = server.start_all()
    assert isinstance(result, tuple)
    assert result[1] == 0
    assert 'started' in result[0]
    assert len(result[0]['started']) == 1
    assert 'already running' in result[0]
    assert len(result[0]['already running']) == 0
    assert 'failed' in result[0]
    assert len(result[0]['failed']) == 1
    ctx['failed_server'] = result[0]['failed'][0]

def test_start_server_2():
    result = server.start({'server-name':ctx['failed_server'],'server-port':19112})
    assert isinstance(result, tuple)
    assert result[1] == 0
    assert "server-name" in result[0]
    assert isinstance(result[0]["server-name"], str)
    assert result[0]["server-name"] == ctx['failed_server']
    assert "state" in result[0]
    assert isinstance(result[0]["state"], str)
    assert result[0]["state"] == 'started'

def test_get_current_world():
    result = world.get_current_world('test-server-1')
    assert isinstance(result, tuple)
    assert result[1] == 0
    assert 'server-name' in result[0]
    assert result[0]['server-name'] == 'test-server-1'
    assert 'level-name' in result[0]
    assert result[0]['level-name'] == 'level-1'

def test_remove_world_fail():
    result = world.remove()
    assert isinstance(result, tuple)
    assert result[1] == 3031  # server-name required

    result = world.remove('blubb')
    assert isinstance(result, tuple)
    assert result[1] == 3032  # server not exists

    result = world.remove('test-server-1', 'blubb')
    assert isinstance(result, tuple)
    assert result[1] == 3033  # world not exists

    result = world.remove('test-server-1')
    assert isinstance(result, tuple)
    assert result[1] == 3034  # server is running

    result = world.remove('test-server-1', 'level-1')
    assert isinstance(result, tuple)
    assert result[1] == 3034  # server is running

def test_remove_server_fail():
    result = server.remove()
    assert isinstance(result, tuple)
    assert result[1] == 1141  # server-name is required

    result = server.remove('blubb')
    assert isinstance(result, tuple)
    assert result[1] == 1142  # server not exists

    result = server.remove('test-server-1')
    assert isinstance(result, tuple)
    assert result[1] == 1143  # server is running

def test_create_backup_fail():
    result = backup.create()
    assert isinstance(result, tuple)
    assert result[1] == 2011  # server-name is required

    result = backup.create('blubb')
    assert isinstance(result, tuple)
    assert result[1] == 2012  # server not exists

    result = backup.create('test-server-1')
    assert isinstance(result, tuple)
    assert result[1] == 2014  # server is running

def test_stop_server_2():
    result = server.stop('test-server-1')
    assert isinstance(result, tuple)
    assert result[1] == 0
    assert 'server-name' in result[0]
    assert result[0]['server-name'] == 'test-server-1'
    assert 'state' in result[0]
    assert result[0]['state'] == 'stopped'

def test_list_backups_empty():
    result = backup.list()
    assert isinstance(result, tuple)
    assert result[1] == 0
    assert isinstance(result[0], dict)
    assert len(result[0]) == 0

def test_create_backup():
    result = backup.create('test-server-1', 'blubb')
    assert isinstance(result, tuple)
    assert result[1] == 2013  # world not exists

    result = backup.create('test-server-1', 'level-1', 'backup-1')  # with given backup-name
    assert isinstance(result, tuple)
    assert result[1] == 0
    assert "server-name" in result[0]
    assert isinstance(result[0]["server-name"], str)
    assert result[0]["server-name"] == 'test-server-1'
    assert "level-name" in result[0]
    assert isinstance(result[0]["level-name"], str)
    assert result[0]["level-name"] == 'level-1'
    assert "backup-name" in result[0]
    assert isinstance(result[0]["backup-name"], str)
    assert result[0]["backup-name"] == 'backup-1'

    result = backup.create('test-server-1', None, 'backup-1')  # with current world
    assert isinstance(result, tuple)
    assert result[1] == 2015  # backup already exists

    result = backup.create('test-server-1', 'level-1', 'backup-1', True)  # overwrite
    assert isinstance(result, tuple)
    assert result[1] == 0

def test_list_backups():
    result = backup.list()
    assert isinstance(result, tuple)
    assert result[1] == 0
    assert len(result[0]) == 1
    assert 'backup-1' in result[0]
    assert "server-name" in result[0]['backup-1']
    assert isinstance(result[0]['backup-1']["server-name"], str)
    assert result[0]['backup-1']["server-name"] == 'test-server-1'
    assert "level-name" in result[0]['backup-1']
    assert isinstance(result[0]['backup-1']["level-name"], str)
    assert result[0]['backup-1']["level-name"] == 'level-1'
    assert "backup-name" in result[0]['backup-1']
    assert isinstance(result[0]['backup-1']["backup-name"], str)
    assert result[0]['backup-1']["backup-name"] == 'backup-1'

def test_remove_world():
    result = world.remove('test-server-1')
    assert isinstance(result, tuple)
    assert result[1] == 0

    result = world.remove('test-server-1', 'level-1')
    assert isinstance(result, tuple)
    assert result[1] == 3033  # world not exists

def test_restore_backup():
    result = backup.restore()
    assert isinstance(result, tuple)
    assert result[1] == 2021  # server-name is required

    result = backup.restore('blubb')
    assert isinstance(result, tuple)
    assert result[1] == 2022  # server not exists

    result = backup.restore('backup-1','test-server-2','Bedrock level')
    assert isinstance(result, tuple)
    assert result[1] == 2025  # world is running

    result = backup.restore('backup-1','test-server-2','level-2')
    assert isinstance(result, tuple)
    assert result[1] == 0
    assert "server-name" in result[0]
    assert isinstance(result[0]["server-name"], str)
    assert result[0]["server-name"] == 'test-server-2'
    assert "level-name" in result[0]
    assert isinstance(result[0]["level-name"], str)
    assert result[0]["level-name"] == 'level-2'
    assert "backup-name" in result[0]
    assert isinstance(result[0]["backup-name"], str)
    assert result[0]["backup-name"] == 'backup-1'

    result = backup.restore('backup-1','test-server-2','level-2')
    assert isinstance(result, tuple)
    assert result[1] == 0

    result = backup.restore('backup-1','test-server-1','level-3')
    assert isinstance(result, tuple)
    assert result[1] == 0
    assert "server-name" in result[0]
    assert isinstance(result[0]["server-name"], str)
    assert result[0]["server-name"] == 'test-server-1'
    assert "level-name" in result[0]
    assert isinstance(result[0]["level-name"], str)
    assert result[0]["level-name"] == 'level-3'
    assert "backup-name" in result[0]
    assert isinstance(result[0]["backup-name"], str)
    assert result[0]["backup-name"] == 'backup-1'

def test_get_worlds_2():
    result = world.list('test-server-2')
    assert isinstance(result, tuple)
    assert result[1] == 0
    assert len(result[0]['worlds']) == 2
    assert 'Bedrock level' in result[0]['worlds']
    assert 'level-2' in result[0]['worlds']

    result = world.list('test-server-1')
    assert isinstance(result, tuple)
    assert result[1] == 0
    assert len(result[0]['worlds']) == 1
    assert 'level-3' in result[0]['worlds']

def test_remove_backup():
    result = backup.remove()
    assert isinstance(result, tuple)
    assert result[1] == 2041  # backup-name is required

    result = backup.remove('blubb')
    assert isinstance(result, tuple)
    assert result[1] == 2042  # backup not exists

def test_remove_server():
    result = server.remove('test-server-1')
    assert isinstance(result, tuple)
    assert result[1] == 0
