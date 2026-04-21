import argparse
import os

from law_mcp.server import mcp


def _configure_transport_security(port: int) -> None:
    from mcp.server.transport_security import TransportSecuritySettings

    allowed = os.environ.get("LAWMCP_ALLOWED_HOSTS", "").split(",")
    allowed = [h.strip() for h in allowed if h.strip()]
    allowed.append(f"localhost:{port}")
    allowed.append(f"127.0.0.1:{port}")

    mcp.settings.transport_security = TransportSecuritySettings(
        enable_dns_rebinding_protection=bool(allowed),
        allowed_hosts=allowed,
    )


def main():
    parser = argparse.ArgumentParser(description="LawMCP - MCP server for Polish legal databases")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="Transport type (default: stdio)",
    )
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port (default: 8000)")
    args = parser.parse_args()

    if args.transport in ("sse", "streamable-http"):
        mcp.settings.host = args.host
        mcp.settings.port = args.port
        _configure_transport_security(args.port)
        mcp.run(transport=args.transport)
    else:
        mcp.run()
