# Bedrock API Server

The Bedrock API Server is a lightweight Python application designed to manage and control multiple Minecraft-Bedrock servers through a simple RESTful API.

## Features

- **Start and Stop Servers**: Easily start and stop Minecraft Bedrock servers with simple API endpoints.
- **Manage Multiple Servers**: Control multiple Bedrock servers independently, each running in its own screen session.
- **RESTful API**: Provides a simple and intuitive API for managing server instances, allowing for easy integration with other tools and services.

## Getting Started

To get started with the Bedrock API Server, follow these steps:

1. **Clone the Repository**: Clone this repository to your local machine.

2. **Build the image**: Since there is no ready-made Docker image in the Docker Hub yet, you still have to build the image yourself.
```bash
docker build --tag bedrock-api-server:latest .
```

3. **start image**: The api is immediately available a few seconds after starting. A port must be specified at startup so that the api can be addressed.
```bash
docker run --rm -d -p 8177:8177 bedrock-api-server:latest .
```

4. **Interact with the API**: Once the server is running, you can interact with the API endpoints to manage your Bedrock servers, similar to this:
```text
POST http://<YOUR_DOCKER_IP>:8177/api-v1/start_server

POST data:
{
  "server-name": "test-server"
}
```

## API Documentation

The following functions are already available:
- `api-v1/get_online_server_version` - Returns the latest bedrock-version from minecraft.net
- `api-v1/get_latest_server_version` - Returns the latest known version, without online retrieval.
- `api-v1/get_downloaded_server_version` - Returns the latest locally available version number.
- `api-v1/download_server` - Downloads the server-binaries of a specified bedrock-version from minecraft.azureedge.net.
- `api-v1/create_server` - Creates a bedrock-server locally with passed server-name and server-version.
- `api-v1/start_server` - Starts a locally created Bedrock server by server-name.
- `api-v1/stop_server` - Stops a running bedrock server by server-name.
- `api-v1/remove_server` - Deletes a locally created server using the server-name.
- `api-v1/get_server_list` - Gives a list of locally available bedrock-servers. Enclosed is also a status for each server.
- `api-v1/say_to_server` - Passes a message to the players on the bedrock-server.

## Contributing

Contributions to the Bedrock API Server project are welcome! If you find any bugs or have suggestions for new features, please open an issue or submit a pull request on GitHub. Go easy on me, this is my first Python project.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

