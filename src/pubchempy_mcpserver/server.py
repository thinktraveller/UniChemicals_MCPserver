import os
import json
from typing import List, Optional, Any
from mcp.server.fastmcp import FastMCP
import pubchempy as pcp

mcp = FastMCP("PubChemPy_MCP_Server")

# --- Helper functions ---
def _safe_execute(func, *args, **kwargs) -> str:
    try:
        result = func(*args, **kwargs)
        if hasattr(result, "to_dict"):
            return json.dumps(result.to_dict(), indent=2)
        elif isinstance(result, list) and len(result) > 0 and hasattr(result[0], "to_dict"):
            return json.dumps([r.to_dict() for r in result], indent=2)
        else:
            return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def get_compounds_by_cid(identifier: int, searchtype: Optional[str] = None) -> str:
    """Search for standardized compound records by cid."""
    return _safe_execute(pcp.get_compounds, identifier, "cid", searchtype=searchtype)

@mcp.tool()
def get_compounds_by_name(identifier: str, searchtype: Optional[str] = None) -> str:
    """Search for standardized compound records by name."""
    return _safe_execute(pcp.get_compounds, identifier, "name", searchtype=searchtype)

@mcp.tool()
def get_compounds_by_smiles(identifier: str, searchtype: Optional[str] = None) -> str:
    """Search for standardized compound records by smiles."""
    return _safe_execute(pcp.get_compounds, identifier, "smiles", searchtype=searchtype)

@mcp.tool()
def get_compounds_by_sdf(identifier: str, searchtype: Optional[str] = None) -> str:
    """Search for standardized compound records by sdf."""
    return _safe_execute(pcp.get_compounds, identifier, "sdf", searchtype=searchtype)

@mcp.tool()
def get_compounds_by_inchi(identifier: str, searchtype: Optional[str] = None) -> str:
    """Search for standardized compound records by inchi."""
    return _safe_execute(pcp.get_compounds, identifier, "inchi", searchtype=searchtype)

@mcp.tool()
def get_compounds_by_inchikey(identifier: str, searchtype: Optional[str] = None) -> str:
    """Search for standardized compound records by inchikey."""
    return _safe_execute(pcp.get_compounds, identifier, "inchikey", searchtype=searchtype)

@mcp.tool()
def get_compounds_by_formula(identifier: str, searchtype: Optional[str] = None) -> str:
    """Search for standardized compound records by formula."""
    return _safe_execute(pcp.get_compounds, identifier, "formula", searchtype=searchtype)

@mcp.tool()
def get_substances_by_sid(sid: int) -> str:
    """Search for raw substance records by sid."""
    return _safe_execute(pcp.get_substances, sid, "sid")

@mcp.tool()
def get_substances_by_name(name: str) -> str:
    """Search for raw substance records by name."""
    return _safe_execute(pcp.get_substances, name, "name")

@mcp.tool()
def get_substances_by_sourceid(sourceid: str, source_name: str) -> str:
    """Search for raw substance records by sourceid and source name."""
    namespace = f"sourceid/{source_name}"
    return _safe_execute(pcp.get_substances, sourceid, namespace)

@mcp.tool()
def get_assays_by_aid(aid: int) -> str:
    """Search for bioassay records by aid."""
    return _safe_execute(pcp.get_assays, aid, "aid")

@mcp.tool()
def get_properties_by_cid(properties: List[str], identifier: int, searchtype: Optional[str] = None) -> str:
    """Retrieve specific properties for compounds identified by cid.
    Properties can be: MolecularFormula, MolecularWeight, InChI, CanonicalSMILES, IsomericSMILES, XLogP, etc."""
    return _safe_execute(pcp.get_properties, properties, identifier, "cid", searchtype=searchtype)

@mcp.tool()
def get_properties_by_name(properties: List[str], identifier: str, searchtype: Optional[str] = None) -> str:
    """Retrieve specific properties for compounds identified by name.
    Properties can be: MolecularFormula, MolecularWeight, InChI, CanonicalSMILES, IsomericSMILES, XLogP, etc."""
    return _safe_execute(pcp.get_properties, properties, identifier, "name", searchtype=searchtype)

@mcp.tool()
def get_properties_by_smiles(properties: List[str], identifier: str, searchtype: Optional[str] = None) -> str:
    """Retrieve specific properties for compounds identified by smiles.
    Properties can be: MolecularFormula, MolecularWeight, InChI, CanonicalSMILES, IsomericSMILES, XLogP, etc."""
    return _safe_execute(pcp.get_properties, properties, identifier, "smiles", searchtype=searchtype)

@mcp.tool()
def get_properties_by_sdf(properties: List[str], identifier: str, searchtype: Optional[str] = None) -> str:
    """Retrieve specific properties for compounds identified by sdf.
    Properties can be: MolecularFormula, MolecularWeight, InChI, CanonicalSMILES, IsomericSMILES, XLogP, etc."""
    return _safe_execute(pcp.get_properties, properties, identifier, "sdf", searchtype=searchtype)

@mcp.tool()
def get_properties_by_inchi(properties: List[str], identifier: str, searchtype: Optional[str] = None) -> str:
    """Retrieve specific properties for compounds identified by inchi.
    Properties can be: MolecularFormula, MolecularWeight, InChI, CanonicalSMILES, IsomericSMILES, XLogP, etc."""
    return _safe_execute(pcp.get_properties, properties, identifier, "inchi", searchtype=searchtype)

@mcp.tool()
def get_properties_by_inchikey(properties: List[str], identifier: str, searchtype: Optional[str] = None) -> str:
    """Retrieve specific properties for compounds identified by inchikey.
    Properties can be: MolecularFormula, MolecularWeight, InChI, CanonicalSMILES, IsomericSMILES, XLogP, etc."""
    return _safe_execute(pcp.get_properties, properties, identifier, "inchikey", searchtype=searchtype)

@mcp.tool()
def get_properties_by_formula(properties: List[str], identifier: str, searchtype: Optional[str] = None) -> str:
    """Retrieve specific properties for compounds identified by formula.
    Properties can be: MolecularFormula, MolecularWeight, InChI, CanonicalSMILES, IsomericSMILES, XLogP, etc."""
    return _safe_execute(pcp.get_properties, properties, identifier, "formula", searchtype=searchtype)

@mcp.tool()
def get_synonyms_by_cid(identifier: int) -> str:
    """Retrieve synonyms (alternative names) for compounds identified by cid."""
    return _safe_execute(pcp.get_synonyms, identifier, "cid")

@mcp.tool()
def get_synonyms_by_name(identifier: str) -> str:
    """Retrieve synonyms (alternative names) for compounds identified by name."""
    return _safe_execute(pcp.get_synonyms, identifier, "name")

@mcp.tool()
def get_synonyms_by_smiles(identifier: str) -> str:
    """Retrieve synonyms (alternative names) for compounds identified by smiles."""
    return _safe_execute(pcp.get_synonyms, identifier, "smiles")

@mcp.tool()
def get_synonyms_by_sdf(identifier: str) -> str:
    """Retrieve synonyms (alternative names) for compounds identified by sdf."""
    return _safe_execute(pcp.get_synonyms, identifier, "sdf")

@mcp.tool()
def get_synonyms_by_inchi(identifier: str) -> str:
    """Retrieve synonyms (alternative names) for compounds identified by inchi."""
    return _safe_execute(pcp.get_synonyms, identifier, "inchi")

@mcp.tool()
def get_synonyms_by_inchikey(identifier: str) -> str:
    """Retrieve synonyms (alternative names) for compounds identified by inchikey."""
    return _safe_execute(pcp.get_synonyms, identifier, "inchikey")

@mcp.tool()
def get_synonyms_by_formula(identifier: str) -> str:
    """Retrieve synonyms (alternative names) for compounds identified by formula."""
    return _safe_execute(pcp.get_synonyms, identifier, "formula")

@mcp.tool()
def get_cids_by_name(identifier: str, searchtype: Optional[str] = None) -> str:
    """Retrieve Compound Identifiers (CIDs) for the specified query by name."""
    return _safe_execute(pcp.get_cids, identifier, "name", searchtype=searchtype)

@mcp.tool()
def get_cids_by_smiles(identifier: str, searchtype: Optional[str] = None) -> str:
    """Retrieve Compound Identifiers (CIDs) for the specified query by smiles."""
    return _safe_execute(pcp.get_cids, identifier, "smiles", searchtype=searchtype)

@mcp.tool()
def get_cids_by_inchi(identifier: str, searchtype: Optional[str] = None) -> str:
    """Retrieve Compound Identifiers (CIDs) for the specified query by inchi."""
    return _safe_execute(pcp.get_cids, identifier, "inchi", searchtype=searchtype)

@mcp.tool()
def get_cids_by_inchikey(identifier: str, searchtype: Optional[str] = None) -> str:
    """Retrieve Compound Identifiers (CIDs) for the specified query by inchikey."""
    return _safe_execute(pcp.get_cids, identifier, "inchikey", searchtype=searchtype)

@mcp.tool()
def get_cids_by_formula(identifier: str, searchtype: Optional[str] = None) -> str:
    """Retrieve Compound Identifiers (CIDs) for the specified query by formula."""
    return _safe_execute(pcp.get_cids, identifier, "formula", searchtype=searchtype)

@mcp.tool()
def get_sids_by_cid(identifier: int) -> str:
    """Retrieve Substance Identifiers (SIDs) for the specified query by cid."""
    return _safe_execute(pcp.get_sids, identifier, "cid")

@mcp.tool()
def get_sids_by_name(identifier: str) -> str:
    """Retrieve Substance Identifiers (SIDs) for the specified query by name."""
    return _safe_execute(pcp.get_sids, identifier, "name")

@mcp.tool()
def get_aids_by_cid(identifier: int) -> str:
    """Retrieve Assay Identifiers (AIDs) for the specified query by cid."""
    return _safe_execute(pcp.get_aids, identifier, "cid")

@mcp.tool()
def get_aids_by_name(identifier: str) -> str:
    """Retrieve Assay Identifiers (AIDs) for the specified query by name."""
    return _safe_execute(pcp.get_aids, identifier, "name")

@mcp.tool()
def download_by_cid(identifier: int, outformat: str, path: str, overwrite: Optional[bool] = False) -> str:
    """Download compound records identified by cid and save to a file.
    outformat can be: XML, JSON, SDF, CSV, PNG, TXT."""
    try:
        pcp.download(outformat, path, identifier, "cid", overwrite=overwrite)
        return f"Successfully downloaded to {path}"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def download_by_name(identifier: str, outformat: str, path: str, overwrite: Optional[bool] = False) -> str:
    """Download compound records identified by name and save to a file.
    outformat can be: XML, JSON, SDF, CSV, PNG, TXT."""
    try:
        pcp.download(outformat, path, identifier, "name", overwrite=overwrite)
        return f"Successfully downloaded to {path}"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def download_by_smiles(identifier: str, outformat: str, path: str, overwrite: Optional[bool] = False) -> str:
    """Download compound records identified by smiles and save to a file.
    outformat can be: XML, JSON, SDF, CSV, PNG, TXT."""
    try:
        pcp.download(outformat, path, identifier, "smiles", overwrite=overwrite)
        return f"Successfully downloaded to {path}"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def download_by_sdf(identifier: str, outformat: str, path: str, overwrite: Optional[bool] = False) -> str:
    """Download compound records identified by sdf and save to a file.
    outformat can be: XML, JSON, SDF, CSV, PNG, TXT."""
    try:
        pcp.download(outformat, path, identifier, "sdf", overwrite=overwrite)
        return f"Successfully downloaded to {path}"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def download_by_inchi(identifier: str, outformat: str, path: str, overwrite: Optional[bool] = False) -> str:
    """Download compound records identified by inchi and save to a file.
    outformat can be: XML, JSON, SDF, CSV, PNG, TXT."""
    try:
        pcp.download(outformat, path, identifier, "inchi", overwrite=overwrite)
        return f"Successfully downloaded to {path}"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def download_by_inchikey(identifier: str, outformat: str, path: str, overwrite: Optional[bool] = False) -> str:
    """Download compound records identified by inchikey and save to a file.
    outformat can be: XML, JSON, SDF, CSV, PNG, TXT."""
    try:
        pcp.download(outformat, path, identifier, "inchikey", overwrite=overwrite)
        return f"Successfully downloaded to {path}"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def download_by_formula(identifier: str, outformat: str, path: str, overwrite: Optional[bool] = False) -> str:
    """Download compound records identified by formula and save to a file.
    outformat can be: XML, JSON, SDF, CSV, PNG, TXT."""
    try:
        pcp.download(outformat, path, identifier, "formula", overwrite=overwrite)
        return f"Successfully downloaded to {path}"
    except Exception as e:
        return f"Error: {str(e)}"

def main():
    mcp.run()

if __name__ == "__main__":
    main()
