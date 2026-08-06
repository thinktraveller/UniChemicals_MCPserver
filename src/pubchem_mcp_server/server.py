"""FastMCP server for PubChem database queries (PubChemPy MCP Server)."""

from mcp.server.fastmcp import FastMCP

from .registry import register_all

mcp = FastMCP("PubChemPy_MCP_Server")

# Register all tools from the declarative registry.
register_all(mcp)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
