# Bedrock API Server

The Bedrock API Server is a lightweight Python application designed to manage and control multiple Minecraft-Bedrock servers through a simple RESTful API. The API interface also enables easy control and monitoring of the Bedrock server via HomeAssistant.

## Features

- **Start and Stop Servers**: Easily start and stop Minecraft Bedrock servers with simple API endpoints.
- **Manage Multiple Servers**: Control multiple Bedrock servers independently, each running in its own screen session.
- **RESTful API**: Provides a simple and intuitive API for managing server instances, allowing for easy integration with other tools and services.
- **Simple CLI**: All API functions are also available for the CLI.

## Getting Started

To get started with the Bedrock API Server, follow these steps:

1. **Pull Docker image**: Clone this repository to your local machine.
   ```bash
   docker pull schonny/bedrock-api-server:latest
   ```

2. **Start Docker image**: The api is immediately available a few seconds after starting. The port (8177) must be specified at startup so that the api can be addressed. You must release at least one additional port (19132) so that you can also play on the bedrock-server.
   ```bash
   docker run \
     --rm \
     --detach \
     --publish 8177:8177 \
     --publish 19132:19132/udp \
     --name bedrock-api-server \
     schonny/bedrock-api-server:latest
   ```

   If you need more Bedrock servers, you also need more ports. Here as an example with max 4 Bedrock servers:
   ```bash
     --publish 19132-19135:19132-19135/udp
   ```

3. **Use volumes to save your data**: There are 4 directories that you can mount as a volume, but they are all in the same root directory. This is the directory structure:
   ```text
   └─┬─ /entrypoint/
     ├─┬─ backups/
     │ └─── incremental/
     ├─── downloaded_server/
     ├─── logs/
     └─── server/
   ```
   You can simply mount all directories by adding only the root directory in Docker:
   ```bash
     --volume /your/host/path/:/entrypoint/
   ```
   Or each directory individually, or only what you need:
   ```bash
     --volume /your/bedrock/backup/path/:/entrypoint/backups/
     --volume /your/bedrock/binaries/path/:/entrypoint/downloaded_server/
     --volume /your/bedrock/log/path/:/entrypoint/logs/
     --volume /your/bedrock/server/path/:/entrypoint/server/
   ```

4. **Using functions**: This Docker image provides two ways to interact with the provided functionalities. The RESTful API allows the functions to be called remotely via HTTP. The CLI (command-line interface), on the other hand, offers direct access via the console. Both interfaces contain the same functions and can be used simultaneously.

   **API-v1**<br>
   `http://<your_ip>:8177/api-v1/<function_name>`<br>
   All parameters are always passed as a json-object in an HTTP-POST:
   ```json
    {
        "server-name":"my-own-server"
    }
   ```

   **CLI-v1**<br>
   ```bash
   # connect to running image
   docker exec -it bedrock-api-server bash
   
   python cli-v1.py <function_name> <parameters>
   ```

5. **The shortest way to play**: This image is not a self-runner. You have to perform every action yourself in order to play Minecraft. At least these steps are required for a simple server start:
- `download-server` - Without specifying a "server-version", the latest stable version is downloaded.
- `create-server` - A "server-name" must be transferred so that the server can be created. This name can no longer be changed for this server. All other parameters (see server.properties) are also configured as server-default-values for this server instance.
- `start-server` - Here, too, at least the "server-name" must be specified. Each additional parameter (see server.properties) will overwrite the minecraft-default-values and server-default-values.


## The following functions are already available
Server functions:
- `get-online-server-version` - Returns the latest bedrock-version from minecraft.net
- `get-downloaded-server-versions` - Returns a list of locally available version numbers.
- `download-server` - Downloads the server-binaries of a specified bedrock-version from minecraft.azureedge.net.
- `create-server` - Creates a bedrock-server locally with passed server-name and server-version.
- `start-server` - Starts a locally created bedrock-server by server-name.
- `stop-server` - Stops a running bedrock-server by server-name.
- `remove-server` - Deletes a locally created server using the server-name.
- `update-server` - Updates a locally created server using the server-name.
- `get-server-list` - Gives a list of locally available bedrock-servers. Enclosed is also a status for each server.
- `say-to-server` - Passes a message to the players on the bedrock-server.
- `send-command` - Sends a Minecraft-command to the bedrock-server. This endpoint allows you to execute commands on the server remotely.
- `get-server-details` - Provides all information about a server.
- `start-server-simple` - Starts a server as it was last running and without rewriting the server-properties.
- `start-all-server` - Try to start all servers as they were last running.
- `stop-all-server` - All running bedrock-servers will be stopped.
- `update-all-server` - All stopped bedrock-servers are updated when an update is available.

World functions:
- `get-worlds` - Retrieves a list of worlds available on the bedrock-server.
- `remove-world` - Removes a specified world from the bedrock-server.

Backup functions:
- `create-backup` - Creates a backup of the specified world of bedrock-server.
- `restore-backup` - Restores a world-backup to a specified bedrock-server.
- `get-backup-list` - Retrieves a list of available world-backups.
- `remove-backup` - Deletes a specified world-backup.
- `backup-all-server` - Creates a backup of the specified worlds of all created bedrock-server.

Player functions:
- `get-known-players` - Lists all players who have ever played on a created bedrock-server.
- `add-player` - Complete your player-list yourself.
- `update-permission` - Edit permissions.json for bedrock-server.
- `update-allowlist`- Remove an existing player from allowlist (white-list).

Jobber functions:
- `start-jobber` - Starts the Jobber service and all contained jobs.
- `stop-jobber` - Stops the Jobber service.
- `get-jobber-config` - Gets the complete Jobber configuration in JSON format.
- `set-jobber-config` - This can be used to import an updated Jobber configuration.
- `restart-jobber` - Restarts the Jobber service so that a new configuration is loaded.
- `list-jobs` - Lists all registered jobs.
- `pause-job` - This can be used to temporarily pause a single job. But beware: When the Jobber service is restarted, the paused job also starts.
- `resume-job` - This reactivates a paused job.
- `run-job` - This function can be used to start any job directly.

## Jobber integration
Jobber is comparable to crontab. Jobs can be defined that are executed at specific times.<br>
Two jobs are already predefined in this image, but these can be changed or deleted as required.
- The first job starts all available bedrock-servers at 12 noon.
- The second job stops all running Bedrock servers at midnight and performs a backup of the worlds as well as an update of the servers.

## Contributing
Contributions to the Bedrock API Server project are welcome! If you find any bugs or have suggestions for new features, please open an issue or submit a pull request on GitHub. Go easy on me, this is my first Python project.

## License
This project is licensed under the Apache-2.0 License. See the [LICENSE](LICENSE) file for details.

