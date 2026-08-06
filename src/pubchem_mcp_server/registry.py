"""Tool registry: declarative specs and factories that generate MCP tools.

Tool names follow the convention ``{database}_{action}_{entity}_by_{identifier}``,
e.g. ``pubchem_search_compound_by_cid``. Actions:

- ``search``: find records (compound / substance / assay)
- ``get``: retrieve attributes (properties / synonyms)
- ``resolve``: convert identifiers (CID / SID / AID)

Adding a new identifier namespace is a one-line change.
"""

from typing import Any, Callable, List, Optional

from . import client
from .utils import safe_execute

# Namespaces whose identifier is an integer (CID / SID / AID).
INT_NAMESPACES = {"cid", "sid", "aid"}

# Namespaces usable for standardized compound records.
COMPOUND_NAMESPACES = ["cid", "name", "smiles", "sdf", "inchi", "inchikey", "formula"]

# Namespaces for identifier resolution tools.
CID_NAMESPACES = ["name", "smiles", "inchi", "inchikey", "formula"]
SID_NAMESPACES = ["cid", "name"]
AID_NAMESPACES = ["cid", "name"]

# Namespaces for raw substance records.
SUBSTANCE_NAMESPACES = ["sid", "name"]


def _id_type(namespace: str) -> type:
    return int if namespace in INT_NAMESPACES else str


def _make_compound_search(namespace: str) -> Callable[..., str]:
    id_type = _id_type(namespace)
    doc = (
        f"Search PubChem standardized compound records by {namespace}.\n\n"
        f"- identifier: the {namespace} value (int for cid, str for others)\n"
        "- searchtype: optional advanced search type "
        "(substructure / superstructure / similarity)\n\n"
        "Returns a JSON string of matching records, or Error: <message>."
    )

    def tool(identifier: id_type, searchtype: Optional[str] = None) -> str:
        return safe_execute(client.get_compounds, identifier, namespace, searchtype=searchtype)

    tool.__name__ = f"pubchem_search_compound_by_{namespace}"
    tool.__doc__ = doc
    return tool


def _make_property_tool(namespace: str) -> Callable[..., str]:
    id_type = _id_type(namespace)
    doc = (
        f"Get PubChem compound properties identified by {namespace}.\n\n"
        f"- properties: list of property names, e.g. MolecularFormula, MolecularWeight, "
        "InChI, CanonicalSMILES, IsomericSMILES, XLogP\n"
        f"- identifier: the {namespace} value (int for cid, str for others)\n"
        "- searchtype: optional advanced search type "
        "(substructure / superstructure / similarity)\n\n"
        "Returns a JSON string of the requested properties, or Error: <message>."
    )

    def tool(properties: List[str], identifier: id_type, searchtype: Optional[str] = None) -> str:
        return safe_execute(client.get_properties, properties, identifier, namespace, searchtype=searchtype)

    tool.__name__ = f"pubchem_get_property_by_{namespace}"
    tool.__doc__ = doc
    return tool


def _make_synonym_tool(namespace: str) -> Callable[..., str]:
    id_type = _id_type(namespace)
    doc = (
        f"Get PubChem compound synonyms (alternative names) identified by {namespace}.\n\n"
        f"- identifier: the {namespace} value (int for cid, str for others)\n\n"
        "Returns a JSON string of synonyms, or Error: <message>."
    )

    def tool(identifier: id_type) -> str:
        return safe_execute(client.get_synonyms, identifier, namespace)

    tool.__name__ = f"pubchem_get_synonym_by_{namespace}"
    tool.__doc__ = doc
    return tool


def _make_substance_search(namespace: str) -> Callable[..., str]:
    id_type = _id_type(namespace)
    doc = (
        f"Search PubChem raw substance records by {namespace}.\n\n"
        f"- identifier: the {namespace} value (int for sid, str otherwise)\n\n"
        "Returns a JSON string of matching substance records, or Error: <message>."
    )

    def tool(identifier: id_type) -> str:
        return safe_execute(client.get_substances, identifier, namespace)

    tool.__name__ = f"pubchem_search_substance_by_{namespace}"
    tool.__doc__ = doc
    return tool


def _make_substance_search_by_sourceid() -> Callable[..., str]:
    doc = (
        "Search PubChem raw substance records by source id and source name.\n\n"
        "- sourceid: the identifier assigned by the source\n"
        "- source_name: the name of the depositing source\n\n"
        "Returns a JSON string of matching substance records, or Error: <message>."
    )

    def tool(sourceid: str, source_name: str) -> str:
        return safe_execute(client.get_substances, sourceid, f"sourceid/{source_name}")

    tool.__name__ = "pubchem_search_substance_by_sourceid"
    tool.__doc__ = doc
    return tool


def _make_assay_search() -> Callable[..., str]:
    doc = (
        "Search PubChem bioassay records by aid.\n\n"
        "- aid: the bioassay identifier (integer)\n\n"
        "Returns a JSON string of the matching assay record, or Error: <message>."
    )

    def tool(aid: int) -> str:
        return safe_execute(client.get_assays, aid, "aid")

    tool.__name__ = "pubchem_search_assay_by_aid"
    tool.__doc__ = doc
    return tool


def _make_cid_resolver(namespace: str) -> Callable[..., str]:
    id_type = _id_type(namespace)
    doc = (
        f"Resolve PubChem compound IDs (CIDs) from {namespace}.\n\n"
        f"- identifier: the {namespace} value (str)\n"
        "- searchtype: optional advanced search type "
        "(substructure / superstructure / similarity)\n\n"
        "Returns a JSON string of matching CIDs, or Error: <message>."
    )

    def tool(identifier: id_type, searchtype: Optional[str] = None) -> str:
        return safe_execute(client.get_cids, identifier, namespace, searchtype=searchtype)

    tool.__name__ = f"pubchem_resolve_cid_by_{namespace}"
    tool.__doc__ = doc
    return tool


def _make_sid_resolver(namespace: str) -> Callable[..., str]:
    id_type = _id_type(namespace)
    doc = (
        f"Resolve PubChem substance IDs (SIDs) from {namespace}.\n\n"
        f"- identifier: the {namespace} value (int for cid, str for name)\n\n"
        "Returns a JSON string of matching SIDs, or Error: <message>."
    )

    def tool(identifier: id_type) -> str:
        return safe_execute(client.get_sids, identifier, namespace)

    tool.__name__ = f"pubchem_resolve_sid_by_{namespace}"
    tool.__doc__ = doc
    return tool


def _make_aid_resolver(namespace: str) -> Callable[..., str]:
    id_type = _id_type(namespace)
    doc = (
        f"Resolve PubChem assay IDs (AIDs) from {namespace}.\n\n"
        f"- identifier: the {namespace} value (int for cid, str for name)\n\n"
        "Returns a JSON string of matching AIDs, or Error: <message>."
    )

    def tool(identifier: id_type) -> str:
        return safe_execute(client.get_aids, identifier, namespace)

    tool.__name__ = f"pubchem_resolve_aid_by_{namespace}"
    tool.__doc__ = doc
    return tool


def register_all(mcp: Any) -> None:
    """Register every MCP tool on the given FastMCP instance."""
    for namespace in COMPOUND_NAMESPACES:
        mcp.tool(name=f"pubchem_search_compound_by_{namespace}")(_make_compound_search(namespace))
    for namespace in SUBSTANCE_NAMESPACES:
        mcp.tool(name=f"pubchem_search_substance_by_{namespace}")(_make_substance_search(namespace))
    mcp.tool(name="pubchem_search_substance_by_sourceid")(_make_substance_search_by_sourceid())
    mcp.tool(name="pubchem_search_assay_by_aid")(_make_assay_search())
    for namespace in COMPOUND_NAMESPACES:
        mcp.tool(name=f"pubchem_get_property_by_{namespace}")(_make_property_tool(namespace))
    for namespace in COMPOUND_NAMESPACES:
        mcp.tool(name=f"pubchem_get_synonym_by_{namespace}")(_make_synonym_tool(namespace))
    for namespace in CID_NAMESPACES:
        mcp.tool(name=f"pubchem_resolve_cid_by_{namespace}")(_make_cid_resolver(namespace))
    for namespace in SID_NAMESPACES:
        mcp.tool(name=f"pubchem_resolve_sid_by_{namespace}")(_make_sid_resolver(namespace))
    for namespace in AID_NAMESPACES:
        mcp.tool(name=f"pubchem_resolve_aid_by_{namespace}")(_make_aid_resolver(namespace))
