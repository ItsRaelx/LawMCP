import argparse
import os

from law_mcp.server import mcp


def main():
    parser = argparse.ArgumentParser(description="LawMCP - MCP server for Polish legal databases")
    parser.add_argument("--sse", action="store_true", help="Run with SSE transport instead of stdio")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind SSE server (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port for SSE server (default: 8000)")
    args = parser.parse_args()

    if args.sse:
        from mcp.server.transport_security import TransportSecuritySettings

        allowed = os.environ.get("LAWMCP_ALLOWED_HOSTS", "").split(",")
        allowed = [h.strip() for h in allowed if h.strip()]
        allowed.append(f"localhost:{args.port}")
        allowed.append(f"127.0.0.1:{args.port}")

        mcp.settings.host = args.host
        mcp.settings.port = args.port
        mcp.settings.transport_security = TransportSecuritySettings(
            enable_dns_rebinding_protection=bool(allowed),
            allowed_hosts=allowed,
        )
        mcp.run(transport="sse")
    else:
        mcp.run()
