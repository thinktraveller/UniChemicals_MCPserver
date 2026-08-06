"""Tool registry: declarative specs and factories that generate MCP tools.

Each family of tools (search / properties / synonyms / identifier conversion /
download) is driven by a small namespace list, so adding a new identifier
namespace is a one-line change.
"""

from typing import Any, Callable, List, Optional

from . import client
from .utils import safe_execute

# Namespaces whose identifier is an integer (CID / SID / AID).
INT_NAMESPACES = {"cid", "sid", "aid"}

# Namespaces usable for standardized compound records.
COMPOUND_NAMESPACES = ["cid", "name", "smiles", "sdf", "inchi", "inchikey", "formula"]

# Namespaces for identifier conversion tools.
CID_NAMESPACES = ["name", "smiles", "inchi", "inchikey", "formula"]
SID_NAMESPACES = ["cid", "name"]
AID_NAMESPACES = ["cid", "name"]

# Namespaces for raw substance records.
SUBSTANCE_NAMESPACES = ["sid", "name"]


def _id_type(namespace: str) -> type:
    return int if namespace in INT_NAMESPACES else str


def _make_compound_search(namespace: str) -> Callable[..., str]:
    id_type = _id_type(namespace)

    def tool(identifier: id_type, searchtype: Optional[str] = None) -> str:
        """Search for standardized compound records by identifier namespace."""
        return safe_execute(client.get_compounds, identifier, namespace, searchtype=searchtype)

    tool.__name__ = f"get_compounds_by_{namespace}"
    tool.__doc__ = f"Search for standardized compound records by {namespace}."
    return tool


def _make_property_tool(namespace: str) -> Callable[..., str]:
    id_type = _id_type(namespace)

    def tool(properties: List[str], identifier: id_type, searchtype: Optional[str] = None) -> str:
        """Retrieve specific properties for compounds identified by identifier namespace."""
        return safe_execute(client.get_properties, properties, identifier, namespace, searchtype=searchtype)

    tool.__name__ = f"get_properties_by_{namespace}"
    tool.__doc__ = (
        f"Retrieve specific properties for compounds identified by {namespace}.\n"
        "Properties can be: MolecularFormula, MolecularWeight, InChI, "
        "CanonicalSMILES, IsomericSMILES, XLogP, etc."
    )
    return tool


def _make_synonym_tool(namespace: str) -> Callable[..., str]:
    id_type = _id_type(namespace)

    def tool(identifier: id_type) -> str:
        """Retrieve synonyms (alternative names) for compounds identified by identifier namespace."""
        return safe_execute(client.get_synonyms, identifier, namespace)

    tool.__name__ = f"get_synonyms_by_{namespace}"
    tool.__doc__ = f"Retrieve synonyms (alternative names) for compounds identified by {namespace}."
    return tool


def _make_substance_search(namespace: str) -> Callable[..., str]:
    id_type = _id_type(namespace)

    def tool(identifier: id_type) -> str:
        """Search for raw substance records by identifier namespace."""
        return safe_execute(client.get_substances, identifier, namespace)

    tool.__name__ = f"get_substances_by_{namespace}"
    tool.__doc__ = f"Search for raw substance records by {namespace}."
    return tool


def _make_substance_search_by_sourceid() -> Callable[..., str]:
    def tool(sourceid: str, source_name: str) -> str:
        """Search for raw substance records by sourceid and source name."""
        return safe_execute(client.get_substances, sourceid, f"sourceid/{source_name}")

    tool.__name__ = "get_substances_by_sourceid"
    tool.__doc__ = "Search for raw substance records by sourceid and source name."
    return tool


def _make_assay_search() -> Callable[..., str]:
    def tool(aid: int) -> str:
        """Search for bioassay records by aid."""
        return safe_execute(client.get_assays, aid, "aid")

    tool.__name__ = "get_assays_by_aid"
    tool.__doc__ = "Search for bioassay records by aid."
    return tool


def _make_cid_resolver(namespace: str) -> Callable[..., str]:
    id_type = _id_type(namespace)

    def tool(identifier: id_type, searchtype: Optional[str] = None) -> str:
        """Retrieve Compound Identifiers (CIDs) for the specified query by identifier namespace."""
        return safe_execute(client.get_cids, identifier, namespace, searchtype=searchtype)

    tool.__name__ = f"get_cids_by_{namespace}"
    tool.__doc__ = f"Retrieve Compound Identifiers (CIDs) for the specified query by {namespace}."
    return tool


def _make_sid_resolver(namespace: str) -> Callable[..., str]:
    id_type = _id_type(namespace)

    def tool(identifier: id_type) -> str:
        """Retrieve Substance Identifiers (SIDs) for the specified query by identifier namespace."""
        return safe_execute(client.get_sids, identifier, namespace)

    tool.__name__ = f"get_sids_by_{namespace}"
    tool.__doc__ = f"Retrieve Substance Identifiers (SIDs) for the specified query by {namespace}."
    return tool


def _make_aid_resolver(namespace: str) -> Callable[..., str]:
    id_type = _id_type(namespace)

    def tool(identifier: id_type) -> str:
        """Retrieve Assay Identifiers (AIDs) for the specified query by identifier namespace."""
        return safe_execute(client.get_aids, identifier, namespace)

    tool.__name__ = f"get_aids_by_{namespace}"
    tool.__doc__ = f"Retrieve Assay Identifiers (AIDs) for the specified query by {namespace}."
    return tool


def _make_download(namespace: str) -> Callable[..., str]:
    id_type = _id_type(namespace)

    def tool(
        identifier: id_type,
        outformat: str,
        path: str,
        overwrite: Optional[bool] = False,
    ) -> str:
        """Download compound records identified by identifier namespace and save to a file."""
        try:
            client.download(outformat, path, identifier, namespace, overwrite=overwrite)
            return f"Successfully downloaded to {path}"
        except Exception as exc:  # noqa: BLE001 - tool boundary: errors go back as text
            return f"Error: {str(exc)}"

    tool.__name__ = f"download_by_{namespace}"
    tool.__doc__ = (
        f"Download compound records identified by {namespace} and save to a file.\n"
        "outformat can be: XML, JSON, SDF, CSV, PNG, TXT."
    )
    return tool


def register_all(mcp: Any) -> None:
    """Register every MCP tool on the given FastMCP instance."""
    for namespace in COMPOUND_NAMESPACES:
        mcp.tool(name=f"get_compounds_by_{namespace}")(_make_compound_search(namespace))
    for namespace in SUBSTANCE_NAMESPACES:
        mcp.tool(name=f"get_substances_by_{namespace}")(_make_substance_search(namespace))
    mcp.tool(name="get_substances_by_sourceid")(_make_substance_search_by_sourceid())
    mcp.tool(name="get_assays_by_aid")(_make_assay_search())
    for namespace in COMPOUND_NAMESPACES:
        mcp.tool(name=f"get_properties_by_{namespace}")(_make_property_tool(namespace))
    for namespace in COMPOUND_NAMESPACES:
        mcp.tool(name=f"get_synonyms_by_{namespace}")(_make_synonym_tool(namespace))
    for namespace in CID_NAMESPACES:
        mcp.tool(name=f"get_cids_by_{namespace}")(_make_cid_resolver(namespace))
    for namespace in SID_NAMESPACES:
        mcp.tool(name=f"get_sids_by_{namespace}")(_make_sid_resolver(namespace))
    for namespace in AID_NAMESPACES:
        mcp.tool(name=f"get_aids_by_{namespace}")(_make_aid_resolver(namespace))
    for namespace in COMPOUND_NAMESPACES:
        mcp.tool(name=f"download_by_{namespace}")(_make_download(namespace))
