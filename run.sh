#!/bin/bash


if [[ $# == 0 ]]; then
    # default, start image in service-mode
    echo "
-------------------------------------------------
  schonny/bedrock-api-server

  This docker image starts in service-mode.
  If you want to switch to quickstart-mode,
  take a look at the help.

  docker run --rm schonny/bedrock-api-server -h
-------------------------------------------------
    "
    mkdir -p /entrypoint/logs /var/jobber/0
    python /app/cli_v1.py start-all-server
    python /app/cli_v1.py start-jobber
    python /app/app.py

elif [ "${1,,}" = "bash" ]; then
    # open bash
    $@

elif [[ ${@,,} =~ (-n|-l|--server-name|--level-name) ]]; then
    # default, start image in quickstart-mode
    echo "
-------------------------------------------------
  schonny/bedrock-api-server

  This docker image starts in quickstart-mode.
  If you want to switch to service-mode, simply
  omit the options at the end.

  docker run schonny/bedrock-api-server <opts>
-------------------------------------------------
    "
    # default values
    SERVER_NAME="Dedicated Server"
    LEVEL_NAME="Bedrock level"
    SERVER_PORT=19132
    # get parameters
    while [[ $# > 0 ]]; do
        case "$1" in
            -n|--server-name)      SERVER_NAME="${2}";    shift 2;;
            -n=*|--server-name=*)  SERVER_NAME="${1#*=}"; shift;;
            -l|--level-name)       LEVEL_NAME="${2}";     shift 2;;
            -l=*|--level-name=*)   LEVEL_NAME="${1#*=}";  shift;;
        esac
    done
    # download server
    echo "Get current server-version from internet."
    CURRENT_VERSION="$(python /app/cli_v1.py get-online-server-version | jq '.version' -r)"
    if [ $? -ne 0 ]; then
        echo "Error: Cannot get current server-version" >&2
        exit 1
    fi
    echo "Try to download current server-version '${CURRENT_VERSION}'."
    if ! python /app/cli_v1.py download-server -v "${CURRENT_VERSION}"; then
        echo "Error: Cannot download current server-version" >&2
        exit 1
    fi
    
    # check server exists
    SERVER_VERSION="$(python /app/cli_v1.py get-server-details -n "${SERVER_NAME}" 2>/dev/null | jq '.version' -r)"
    if [ -z "${SERVER_VERSION}" ]; then
        echo "server with name '${SERVER_NAME}' does not exists. it will create tham."
        if ! python /app/cli_v1.py create-server -n "${SERVER_NAME}" -v "${CURRENT_VERSION}" -p level-name "${LEVEL_NAME}"; then
            echo "Error: Cannot create bedrock-server with current server-version" >&2
            exit 1
        fi
    elif [ "${SERVER_VERSION}" != "${CURRENT_VERSION}" ]; then
        echo "server with name '${SERVER_NAME}' already exists but the server-version is outdated."
        if ! python /app/cli_v1.py update-server -n "${SERVER_NAME}" -v "${CURRENT_VERSION}"; then
            echo "Error: Cannot update existing bedrock-server to new server-version" >&2
            exit 1
        fi
    fi

    # start server with given level on port SERVER_PORT
    echo "start server '${SERVER_NAME}' with level '${LEVEL_NAME}' on port ${SERVER_PORT}"
    if ! python /app/cli_v1.py start-server -n "${SERVER_NAME}" -p server-port ${SERVER_PORT} -p level-name "${LEVEL_NAME}"; then
        echo "Error: Cannot start bedrock-server" >&2
        exit 1
    fi

    # start api
    python /app/app.py

else
    echo "
    docker run schonny/bedrock-api-server [options]

    This is the quickstart-mode. In this mode, you can simply start
    the bedrock-server with new worlds (levels) or continue old ones.
    Without options, the Docker container starts in service-mode.

    Options:
    -h | --help | -?             show this help view
    -n | --server-name <STRING>  will start a bedrock-server with
                                 the given name. Default: 'Dedicated Server'
    -l | --level-name <STRING>   will start the given level (world) on
                                 the bedrock-server. Default: 'Bedrock level'

    Examples:
    docker run -p "19132:19132" schonny/bedrock-api-server -n quickstart
        Will start the bedrock-server with the name 'quickstart' and
        the level 'Bedrock level' on port 19132. If the server 'quickstart'
        does not exist, it will create it.

    docker run -p "19132:19132" schonny/bedrock-api-server -l quickstart
        Will start the bedrock-server with the name 'Dedicated Server' and
        the level 'quickstart' on port 19132. If the level 'quickstart'
        does not exist on this server, it will create it.

    Notes:
    -If your bedrock-server is outdated, it will upgrade before starting.
    -In quickstart-mode, the bedrock-server is not backed up.
    -You need at least one option to start the container in quickstart-mode.
    -The created server will store in '/entrypoint/server/<server-name>/'.
    "
 fi
