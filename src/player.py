# player.py
# err:15xx

from datetime import datetime
import os

import helpers
import settings

def get_known():  # 151x
    player_json = os.path.join(settings.SERVER_PATH, 'player.json')
    if os.path.exists(player_json):
        json_result = helpers.read_json(player_json)
        if json_result[1] == 0:
            players = json_result[0]
        else:
            return 'cannot parse player-json', 1511
    return {'players': players}, 0

def add(name, xuid):  # 152x
    if helpers.is_empty(name):
        return '"user-name" is required', 1521
    if helpers.is_empty(xuid):
        return '"xuid" is required', 1522
    
    player_json = os.path.join(settings.SERVER_PATH, 'player.json')
    if os.path.exists(player_json):
        json_result = helpers.read_json(player_json)
        if json_result[1] == 0:
            players = json_result[0]
        else:
            return 'cannot parse player-json', 1523
    else:
        players = []

    for player in players:
        if player['xuid'] == xuid:
            return {
                'name': player['name'],
                'xuid': xuid,
                'state': 'already exists'
            }, 0
    
    players.append({
        'name': name,
        'xuid': xuid,
        'playtime': 0,
        'last-seen': None
    })

    write_result = helpers.write_json(player_json, players)
    if write_result[1] > 0:
        return 'cannot write player-json', 1524
    
    return {
        'name': name,
        'xuid': xuid,
        'state': 'added'
    }, 0

def start_playtime(name, time=None):  # 153x
    if helpers.is_empty(name):
        return '"user-name" is required', 1531
    if helpers.is_empty(time):
        time = datetime.now()
    
    player_json = os.path.join(settings.SERVER_PATH, 'player.json')
    if not os.path.exists(player_json):
        return 'player-json does not exists', 1532
    else:
        json_result = helpers.read_json(player_json)
        if json_result[1] == 0:
            players = json_result[0]
        else:
            return 'cannot parse player-json', 1533

    for player in players:
        if player['name'] == name:
            last_seen = None
            if player['last-seen'] != None:
                last_seen = datetime.strptime(player['last-seen'], '%Y-%m-%d %H:%M:%S')
            if last_seen != None and last_seen >= time:
                return {
                    'name': player['name'],
                    'xuid': player['xuid'],
                    'state': 'up-to-date'
                }, 0
            else:
                player['last-seen'] = time.strftime('%Y-%m-%d %H:%M:%S')

            write_result = helpers.write_json(player_json, players)
            if write_result[1] > 0:
                return 'cannot write player-json', 1534
            
            return {
                'name': player['name'],
                'xuid': player['xuid'],
                'state': 'updated'
            }, 0
    
    return 'player-name not in player-json', 1535

def stop_playtime(name, time=None):  # 154x
    if helpers.is_empty(name):
        return '"user-name" is required', 1541
    if helpers.is_empty(time):
        time = datetime.now()
    
    player_json = os.path.join(settings.SERVER_PATH, 'player.json')
    if not os.path.exists(player_json):
        return 'player-json does not exists', 1542
    else:
        json_result = helpers.read_json(player_json)
        if json_result[1] == 0:
            players = json_result[0]
        else:
            return 'cannot parse player-json', 1543

    for player in players:
        if player['name'] == name:
            last_seen = None
            if player['last-seen'] != None:
                last_seen = datetime.strptime(player['last-seen'], '%Y-%m-%d %H:%M:%S')
            if last_seen != None and last_seen >= time:
                return {
                    'name': player['name'],
                    'xuid': player['xuid'],
                    'state': 'up-to-date'
                }, 0
            else:
                player['playtime'] += (time - last_seen).total_seconds()
                player['last-seen'] = time.strftime('%Y-%m-%d %H:%M:%S')
                print(player)
                print(players)

            write_result = helpers.write_json(player_json, players)
            if write_result[1] > 0:
                return 'cannot write player-json', 1544
            
            return {
                'name': player['name'],
                'xuid': player['xuid'],
                'state': 'updated'
            }, 0
    
    return 'player-name not in player-json', 1545

def update_permission(server_name, name, permission=None):  # 155x
    if helpers.is_empty(server_name):
        return '"server-name" is required', 1551
    if helpers.is_empty(name):
        return '"user-name" is required', 1552
    if permission != None and permission not in ['visitor', 'member', 'operator']:
        return '"permission" has a unexpected value', 1553

    server_path = os.path.join(settings.SERVER_PATH, server_name)
    if not os.path.exists(server_path):
        return f"server with this name '{server_name}' does not exists", 1554
    
    permissions_path = os.path.join(server_path, 'permissions.json')
    json_result = helpers.read_json(permissions_path)
    if json_result[1] > 0:
        return 'cannot read permissions-json', 1555
    permissions = json_result[0]
    print(permissions)

    xuid = None
    player_json = os.path.join(settings.SERVER_PATH, 'player.json')
    if os.path.exists(player_json):
        json_result = helpers.read_json(player_json)
        if json_result[1] == 0:
            for player in json_result[0]:
                if player['name'] == name:
                    xuid = player['xuid']
                    break
        else:
            return 'cannot parse player-json', 1556
    if xuid == None:
        return 'player-name is unknown', 1557

    state = None
    for index, player in enumerate(permissions):
        if ('name' in player and player['name'] == name) or player['xuid'] == xuid:
            if permission == None:
                del permissions[index]
                state = 'removed'
            elif player['permission'] == permission:
                state = 'up-to-date'
            else:
                player['permission'] = permission
                player['name'] = name
                state = 'updated'
            break
        
    if state == None:
        state = 'added'
        permissions.append({
            'name': name,
            'xuid': xuid,
            'permission': permission
        })

    write_result = helpers.write_json(permissions_path, permissions)
    if write_result[1] > 0:
        return 'cannot write permissions-json', 1558
    return {
        'server-name': server_name,
        'player-name': name,
        'permission': permission,
        'state': state
    }, 0