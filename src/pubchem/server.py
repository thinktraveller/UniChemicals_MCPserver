"""FastMCP server for multi-database chemistry queries (PubChem + CAS)."""

from mcp.server.fastmcp import FastMCP

from cas.registry import register_all as register_cas
from pubchem.registry import register_all as register_pubchem

mcp = FastMCP("UniChemicals_MCP_Server")

# Register tools from both database registries.
register_pubchem(mcp)
register_cas(mcp)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
