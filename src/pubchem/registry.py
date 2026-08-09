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
COMPOUND_NAMESPACES = ["cid", "name", "smiles", "inchi", "inchikey", "formula"]

# Namespaces for identifier resolution tools.
CID_NAMESPACES = ["name", "smiles", "inchi", "inchikey", "formula"]
SID_NAMESPACES = ["cid", "name"]
AID_NAMESPACES = ["cid", "name"]

# Namespaces for raw substance records.
SUBSTANCE_NAMESPACES = ["sid", "name"]

# Computed descriptor properties supported by PUG REST (verified live against
# PubChem on 2026-08-07; ``ConformerModel3D`` is not a valid property name).
DEFAULT_DESCRIPTORS = [
    "MolecularFormula",
    "MolecularWeight",
    "ExactMass",
    "MonoisotopicMass",
    "XLogP",
    "TPSA",
    "Complexity",
    "Charge",
    "HBondDonorCount",
    "HBondAcceptorCount",
    "RotatableBondCount",
    "HeavyAtomCount",
    "IsotopeAtomCount",
    "AtomStereoCount",
    "DefinedAtomStereoCount",
    "UndefinedAtomStereoCount",
    "BondStereoCount",
    "DefinedBondStereoCount",
    "UndefinedBondStereoCount",
    "CovalentUnitCount",
    "Volume3D",
]


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


def _make_cids_batch_search() -> Callable[..., str]:
    doc = (
        "Search PubChem standardized compound records by a list of CIDs (batch).\n\n"
        "- cids: list of compound IDs (integers), at most 100 per request\n\n"
        "Returns a JSON string of matching compound records, or Error: <message>."
    )

    def tool(cids: List[int]) -> str:
        return safe_execute(client.get_compounds, cids, "cid")

    tool.__name__ = "pubchem_search_compound_by_cids"
    tool.__doc__ = doc
    return tool


def _make_cids_batch_property() -> Callable[..., str]:
    doc = (
        "Get PubChem compound properties for a list of CIDs (batch).\n\n"
        "- properties: list of property names, e.g. MolecularFormula, MolecularWeight, XLogP\n"
        "- cids: list of compound IDs (integers), at most 100 per request\n\n"
        "Returns a JSON string of the requested properties, or Error: <message>."
    )

    def tool(properties: List[str], cids: List[int]) -> str:
        return safe_execute(client.get_properties, properties, cids, "cid")

    tool.__name__ = "pubchem_get_property_by_cids"
    tool.__doc__ = doc
    return tool


def _make_conformer_tool() -> Callable[..., str]:
    doc = (
        "Get PubChem 3D conformer (3D coordinates) for a compound by cid.\n\n"
        "- cid: the compound identifier (integer)\n\n"
        "Note: not every compound has 3D data; such compounds return an Error: message.\n"
        "Returns a JSON string of the 3D record, or Error: <message>."
    )

    def tool(cid: int) -> str:
        return safe_execute(client.get_conformer, cid)

    tool.__name__ = "pubchem_get_conformer_by_cid"
    tool.__doc__ = doc
    return tool


def _make_descriptor_tool() -> Callable[..., str]:
    doc = (
        "Get PubChem computed descriptors for a compound by cid.\n\n"
        "- cid: the compound identifier (integer)\n"
        "- properties: optional list of descriptor names; defaults to the standard set "
        "(MolecularFormula, MolecularWeight, ExactMass, XLogP, TPSA, Complexity, "
        "HBondDonorCount, HBondAcceptorCount, RotatableBondCount, HeavyAtomCount, ...)\n\n"
        "Returns a JSON string of the requested descriptors, or Error: <message>."
    )

    def tool(cid: int, properties: Optional[List[str]] = None) -> str:
        return safe_execute(client.get_properties, properties or DEFAULT_DESCRIPTORS, cid, "cid")

    tool.__name__ = "pubchem_get_descriptor_by_cid"
    tool.__doc__ = doc
    return tool


def _make_structure_tool() -> Callable[..., str]:
    doc = (
        "Get PubChem compound atom/bond topology (structure) by cid.\n\n"
        "- cid: the compound identifier (integer)\n\n"
        "Returns a JSON string with atoms (aid, element, coordinates) and bonds "
        "(aid1, aid2, order), or Error: <message>."
    )

    def tool(cid: int) -> str:
        return safe_execute(client.get_structure, cid)

    tool.__name__ = "pubchem_get_structure_by_cid"
    tool.__doc__ = doc
    return tool


def _make_spectrum_tool() -> Callable[..., str]:
    doc = (
        "Get PubChem spectral data for a compound by cid.\n\n"
        "- cid: the compound identifier (integer)\n"
        "- spectrum_type: one of 1H NMR, 13C NMR, 1H-13C NMR, GC-MS, MS-MS, LC-MS, "
        "IR, FTIR, ATR-IR, UV, Raman\n\n"
        "Data comes from PubChem PUG-View (Spectral Information heading). "
        "Not every compound has spectral data.\n"
        "Returns a JSON string of the parsed spectra, or Error: <message>."
    )

    def tool(cid: int, spectrum_type: str) -> str:
        return safe_execute(client.get_spectrum, cid, spectrum_type)

    tool.__name__ = "pubchem_get_spectrum_by_cid"
    tool.__doc__ = doc
    return tool


def register_all(mcp: Any) -> None:
    """Register every MCP tool on the given FastMCP instance."""
    for namespace in COMPOUND_NAMESPACES:
        mcp.tool(name=f"pubchem_search_compound_by_{namespace}")(_make_compound_search(namespace))
    for namespace in SUBSTANCE_NAMESPACES:
        mcp.tool(name=f"pubchem_search_substance_by_{namespace}")(_make_substance_search(namespace))
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
    mcp.tool(name="pubchem_search_compound_by_cids")(_make_cids_batch_search())
    mcp.tool(name="pubchem_get_property_by_cids")(_make_cids_batch_property())
    mcp.tool(name="pubchem_get_conformer_by_cid")(_make_conformer_tool())
    mcp.tool(name="pubchem_get_descriptor_by_cid")(_make_descriptor_tool())
    mcp.tool(name="pubchem_get_structure_by_cid")(_make_structure_tool())
    mcp.tool(name="pubchem_get_spectrum_by_cid")(_make_spectrum_tool())
