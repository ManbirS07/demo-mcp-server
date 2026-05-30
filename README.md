## Demo MCP Server

This project defines a FastMCP server in `main.py`.

If you are connecting it to Claude Desktop on Windows, make sure the config points at the project root and starts the server with the workspace virtual environment Python. A working example is:

```json
{
	"mcpServers": {
		"demo server": {
			"command": "uv", //path to the uv executable
			"args": ["main.py"],
			"cwd": "demo-mcp-server"
		}
	}
}
```

After changing the config, fully restart Claude Desktop so it reloads the server list.

Run it with:

```bash
uv run fastmcp run main.py
```

To inspect the server:

```bash
uv run fastmcp inspect main.py
```

If you want the MCP Inspector during development:

```bash
uv run fastmcp dev inspector main.py
```

