# Bedrock API Server

The Bedrock API Server is a lightweight Python application designed to manage and control multiple Minecraft-Bedrock servers through a simple RESTful API.

## Features

- **Start and Stop Servers**: Easily start and stop Minecraft Bedrock servers with simple API endpoints.
- **Manage Multiple Servers**: Control multiple Bedrock servers independently, each running in its own screen session.
- **RESTful API**: Provides a simple and intuitive API for managing server instances, allowing for easy integration with other tools and services.
- **Simple CLI**: All API functions are also available for the CLI.

## Getting Started

To get started with the Bedrock API Server, follow these steps:

1. **Clone the Repository**: Clone this repository to your local machine.

2. **Build the image**: Since there is no ready-made Docker image in the Docker Hub yet, you still have to build the image yourself.
   ```bash
   docker build --tag bedrock-api-server:latest .
   ```

3. **Start image**: The api is immediately available a few seconds after starting. The port (8177) must be specified at startup so that the api can be addressed. You must release at least one additional port (19132) so that you can also play on the bedrock-server.
   ```bash
   # only with one bedrock-port 19132
   docker run --rm -d -p 8177:8177 -p 19132:19132/udp --name bedrock-api-server bedrock-api-server:latest
   
   # for more bedrock-server, you need more ports
   docker run --rm -d -p 8177:8177 -p 19132-19133:19132-19133/udp --name bedrock-api-server bedrock-api-server:latest
   ```

4. **Interact with the API**: Once the server is running, you can interact with the API endpoints to manage your Bedrock servers.<br>
`http://<your_ip>:8177/api-v1/<function_name>`<br>
All parameters are always passed as a json-object in an HTTP-POST:
   ```json
    {
        "server-name":"my-own-server"
    }
   ```

5. **Alternate use CLI**: If the API is too complex for you, you can also execute all functions via the CLI as an alternative.
   ```bash
   # connect to running image
   docker exec -it bedrock-api-server bash
   
   # view help of cli-v1
   python cli-v1.py --help
   ```


## The following functions are already available
Server functions:
- `get-online-server-version` - Returns the latest bedrock-version from minecraft.net
- `get-downloaded-server-versions` - Returns a list of locally available version numbers.
- `download-server` - Downloads the server-binaries of a specified bedrock-version from minecraft.azureedge.net.
- `create-server` - Creates a bedrock-server locally with passed server-name and server-version.
- `start-server` - Starts a locally created Bedrock server by server-name.
- `stop-server` - Stops a running bedrock server by server-name.
- `remove-server` - Deletes a locally created server using the server-name.
- `get-server-list` - Gives a list of locally available bedrock-servers. Enclosed is also a status for each server.
- `say-to-server` - Passes a message to the players on the bedrock-server.
- `send-command` - Sends a Minecraft-command to the bedrock-server. This endpoint allows you to execute commands on the server remotely.
- `get-server-details` - Provides all information about a server.
- `start-server-simple` - Starts a server as it was last running. Only with specified server-name.
- `start-all-server` - Try to start all servers as they were last running.
- `stop-all-server` - All running Bedrock servers will be stopped.

World functions:
- `get-worlds` - Retrieves a list of worlds available on the bedrock-server.
- `remove-world` - Removes a specified world from the bedrock-server.

Backup functions:
- `create-backup` - Creates a backup of the specified world of bedrock-server.
- `restore-backup` - Restores a world-backup to a specified bedrock-server.
- `get-backup-list` - Retrieves a list of available world-backups.
- `remove-backup` - Deletes a specified world-backup.


## The right way
This image is not a self-runner. You have to perform every action yourself in order to play Minecraft. At least these steps are required for a simple server start:
- `download-server` - Without specifying a "server-version", the latest version is downloaded.
- `create-server` - A "server-name" must be transferred so that the server can be created. This name can no longer be changed for this server. All other parameters (see server.properties) are also configured as default-values for this server.
- `start-server` - Here, too, at least the "server-name" must be specified. Each additional parameter (see server.properties) will overwrite the minecraft-default-values.



## Contributing

Contributions to the Bedrock API Server project are welcome! If you find any bugs or have suggestions for new features, please open an issue or submit a pull request on GitHub. Go easy on me, this is my first Python project.

## License

This project is licensed under the Apache-2.0 License. See the [LICENSE](LICENSE) file for details.

