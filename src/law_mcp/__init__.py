import argparse

from law_mcp.server import mcp


def main():
    parser = argparse.ArgumentParser(description="LawMCP - MCP server for Polish legal databases")
    parser.add_argument("--sse", action="store_true", help="Run with SSE transport instead of stdio")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind SSE server (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port for SSE server (default: 8000)")
    args = parser.parse_args()

    if args.sse:
        mcp.settings.host = args.host
        mcp.settings.port = args.port
        mcp.run(transport="sse")
    else:
        mcp.run()
