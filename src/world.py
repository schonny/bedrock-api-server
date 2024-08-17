# world.py
# err:3xxx

#import logging
import os,sys
#import shutil

import helpers
import server
import settings

#import python_nbt.nbt as nbt
#import nbtlib
#from nbt.nbt import NBTFile
#from pybedrock import LevelDB

import gzip
# local module
'''
try:
    import nbt
except ImportError:
    # nbt not in search path. Let's see if it can be found in the parent folder
    extrasearchpath = os.path.realpath(os.path.join(__file__,os.pardir,os.pardir))
    if not os.path.exists(os.path.join(extrasearchpath,'nbt')):
        raise
    sys.path.append(extrasearchpath)
from nbt.nbt import NBTFile, TAG_Long, TAG_Int, TAG_String, TAG_Compound
'''

def list(server_name=None):  # 301x
    if helpers.is_empty(server_name):
        return 'server-name is required', 3011

    server_path = os.path.join(settings.SERVER_PATH, server_name)
    if not os.path.exists(server_path):
        return f"server with this name '{server_name}' does not exists", 3012
    
    worlds_path = os.path.join(settings.SERVER_PATH, server_name, 'worlds')
    try:
        directory_contents = os.listdir(worlds_path)
        directories = [entry for entry in directory_contents if os.path.isdir(os.path.join(worlds_path, entry))]
        
        return {
            'server-name': server_name,
            "worlds": directories
        }, 0
    except OSError as e:
        return {
            'server-name': server_name,
            "worlds": []
        }, 0

def get_current_world(server_name=None):  # 302x
    if helpers.is_empty(server_name):
        return 'server-name is required', 3021

    server_path = os.path.join(settings.SERVER_PATH, server_name)
    if not os.path.exists(server_path):
        return f"server with this name '{server_name}' does not exists", 3022

    properties_file = os.path.join(server_path, 'server.properties')
    if not os.path.exists(properties_file):
        return 'server is never started', 3023
    
    result = helpers.read_properties(os.path.join(settings.SERVER_PATH, server_name, 'server.properties'))
    if result[1] > 0:
        return 'cannot read property-file', 3024

    return {
        'server-name': server_name,
        'level-name': result[0]['level-name']
    }, 0
    
def remove(server_name=None, level_name=None):  # 303x
    if helpers.is_empty(server_name):
        return 'server-name is required', 3031

    server_path = os.path.join(settings.SERVER_PATH, server_name)
    if not os.path.exists(server_path):
        return f"server with this name '{server_name}' does not exists", 3032
    
    result = is_running(server_name, level_name)
    if result[1] > 0:
        return 'error on worlds', 3033, result
    elif result[0]['state']:
        return 'world is in use', 3034
    level_name = result[0]['level-name']

    # remove
    level_path = os.path.join(settings.SERVER_PATH, server_name, 'worlds', level_name)
    result = helpers.remove_dirtree(level_path)
    if result[1] > 0:
        return 'cannot remove world', 3035, result
    return {
        'server-name': server_name,
        'level-name': level_name,
        'state': 'removed'
    }, 0

def is_running(server_name, level_name=None):  # 304x
    result = list(server_name)
    if result[1] > 0:
        return 'no worlds', 3041, result
    worlds = result[0]['worlds']

    if len(worlds) == 0:
        return 'no worlds found', 3042

    result = get_current_world(server_name)
    current_name = result[0]['level-name'] if result[1] == 0 else None
    if helpers.is_empty(level_name):
        level_name = current_name

    if level_name not in worlds:
        return 'the level-name does not exists in this server', 3043
    elif server.is_running(server_name) and level_name == current_name:
        state = True
    else:
        state = False
    return {
        'server-name': server_name,
        'level-name': level_name,
        'state': state
    }, 0

'''
def get_all_members(server_name, level_name=None):  # 305x
    result = list(server_name)
    print(result)
    if result[1] > 0:
        return 'no worlds', 3051, result
    worlds = result[0]['worlds']

    if len(worlds) == 0:
        return 'no worlds found', 3052

    result = get_current_world(server_name)
    current_name = result[0]['level-name'] if result[1] == 0 else None
    if helpers.is_empty(level_name):
        level_name = current_name

    if level_name not in worlds:
        return 'the level-name does not exists in this server', 3053

    level_dat_path = os.path.join(settings.SERVER_PATH, server_name, 'worlds', level_name, 'level.dat')
    level_dat_gzip = os.path.join(settings.SERVER_PATH, server_name, 'worlds', level_name, 'level.dat.gz')
    # Öffne die level.dat-Datei

    os.system(f"gzip -fk '{level_dat_path}'")

    level = NBTFile(level_dat_gzip)
    print(level)

    #with open(level_dat_path, 'rb') as file:
        
    # Lade die NBT-Daten
    nbtfile = nbt.nbt.NBTFile(level_dat_gzip,'rb')
    if not "bukkit" in nbtfile:
        return
    if not "lastPlayed" in nbtfile["bukkit"]:
        return
    print("%s,%s,%s" % ( nbtfile["bukkit"]["lastKnownName"], uuid, nbtfile["bukkit"]["lastPlayed"]))


    nbt_data = nbt.read_from_nbt_file(level_dat_gzip)
    print(nbt_data)
    # Extrahiere die Liste der Spieler aus den NBT-Daten
    player_list = nbt_data['']['']['PlayerList']
    print(player_list)
    members = []
    for player in player_list:
        members.append(player['Name'].value)
        
    return {
        'server-name': server_name,
        'level-name': level_name,
        'members': members
    }, 0
'''