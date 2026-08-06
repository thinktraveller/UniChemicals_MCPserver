"""PubChem data access layer.

Wraps PubChemPy (PUG REST) calls so MCP tools never talk to PubChemPy
directly. PubChemPy uses ``urllib`` internally without an explicit timeout,
so a default socket timeout is applied process-wide to avoid hanging requests.
"""

import socket
import time
from typing import Any, Dict, List, Optional

import pubchempy as pcp
import requests

# PubChem PUG REST request timeout (seconds).
REQUEST_TIMEOUT = 30
socket.setdefaulttimeout(REQUEST_TIMEOUT)

# PUG-View direct REST access (PubChemPy has no spectrum support).
PUG_VIEW_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/{cid}/JSON"
SPECTRUM_HEADING = "Spectral Information"
PUG_VIEW_USER_AGENT = "pubchempy-mcp-server/0.2"
PUG_VIEW_TIMEOUT = 30
PUG_VIEW_RETRIES = 3

# User-friendly spectrum type -> PUG-View TOC heading (verified live 2026-08-07).
SPECTRUM_TYPE_ALIASES = {
    "1h nmr": "1H NMR Spectra",
    "1h": "1H NMR Spectra",
    "13c nmr": "13C NMR Spectra",
    "13c": "13C NMR Spectra",
    "1h-13c nmr": "1H-13C NMR Spectra",
    "1h-13c": "1H-13C NMR Spectra",
    "gc-ms": "GC-MS",
    "gcms": "GC-MS",
    "ms-ms": "MS-MS",
    "msms": "MS-MS",
    "lc-ms": "LC-MS",
    "lcms": "LC-MS",
    "ir": "IR Spectra",
    "ftir": "FTIR Spectra",
    "atr-ir": "ATR-IR Spectra",
    "uv": "UV Spectra",
    "raman": "Raman Spectra",
}


def get_compounds(
    identifier: Any,
    namespace: str = "cid",
    searchtype: Optional[str] = None,
    **kwargs: Any,
) -> Any:
    """Search standardized compound records."""
    return pcp.get_compounds(identifier, namespace, searchtype=searchtype, **kwargs)


def get_properties(
    properties: List[str],
    identifier: Any,
    namespace: str = "cid",
    searchtype: Optional[str] = None,
) -> Any:
    """Retrieve specific properties for compounds."""
    return pcp.get_properties(properties, identifier, namespace, searchtype=searchtype)


def get_synonyms(identifier: Any, namespace: str) -> Any:
    """Retrieve synonyms (alternative names) for compounds."""
    return pcp.get_synonyms(identifier, namespace)


def get_substances(identifier: Any, namespace: str) -> Any:
    """Search raw substance records."""
    return pcp.get_substances(identifier, namespace)


def get_assays(identifier: Any, namespace: str) -> Any:
    """Search bioassay records."""
    return pcp.get_assays(identifier, namespace)


def get_cids(
    identifier: Any,
    namespace: str,
    searchtype: Optional[str] = None,
) -> Any:
    """Resolve identifiers to compound IDs (CIDs)."""
    return pcp.get_cids(identifier, namespace, searchtype=searchtype)


def get_sids(identifier: Any, namespace: str) -> Any:
    """Resolve identifiers to substance IDs (SIDs)."""
    return pcp.get_sids(identifier, namespace)


def get_aids(identifier: Any, namespace: str) -> Any:
    """Resolve identifiers to assay IDs (AIDs)."""
    return pcp.get_aids(identifier, namespace)


def get_structure(identifier: int) -> dict:
    """Return atom/bond topology (structure) for a compound."""
    compounds = pcp.get_compounds(identifier, "cid")
    if not compounds:
        return {"cid": identifier, "atoms": [], "bonds": []}
    compound = compounds[0]
    return {
        "cid": compound.cid,
        "atoms": [vars(atom) for atom in compound.atoms],
        "bonds": [vars(bond) for bond in compound.bonds],
    }


def get_conformer(identifier: int) -> dict:
    """Return 3D conformer data (atoms with 3D coordinates) for a compound.

    Uses ``vars`` instead of ``Compound.to_dict()`` because PubChemPy 1.0.5's
    ``to_dict`` crashes on 3D records where ``fingerprint`` is missing.
    """
    compounds = pcp.get_compounds(identifier, "cid", record_type="3d")
    if not compounds:
        return {"cid": identifier, "atoms": [], "bonds": []}
    compound = compounds[0]
    return {
        "cid": compound.cid,
        "coordinate_type": getattr(compound, "coordinate_type", None),
        "atoms": [vars(atom) for atom in compound.atoms],
        "bonds": [vars(bond) for bond in compound.bonds],
    }


def fetch_pug_view(cid: int, heading: str = SPECTRUM_HEADING) -> dict:
    """Fetch a compound's PUG-View JSON document, retrying transient errors."""
    url = PUG_VIEW_URL.format(cid=cid)
    for attempt in range(PUG_VIEW_RETRIES):
        try:
            resp = requests.get(
                url,
                params={"heading": heading},
                headers={"User-Agent": PUG_VIEW_USER_AGENT},
                timeout=PUG_VIEW_TIMEOUT,
            )
            if resp.status_code == 503 and attempt < PUG_VIEW_RETRIES - 1:
                time.sleep(1 + attempt)
                continue
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException:
            if attempt >= PUG_VIEW_RETRIES - 1:
                raise
            time.sleep(1 + attempt)
    raise RuntimeError("unreachable")


def _extract_information_value(item: dict) -> Any:
    """Extract a human-readable value from a PUG-View Information item."""
    value = item.get("Value")
    if isinstance(value, dict):
        strings = value.get("StringWithMarkup")
        if strings:
            parts = [part.get("String", "") for part in strings if part.get("String")]
            return "; ".join(parts)
        number = value.get("Number")
        if number is not None:
            unit = value.get("Unit")
            return f"{number} {unit}".strip() if unit else number
        external = value.get("ExternalDataURL")
        if external:
            return "; ".join(external)
        if value:
            return str(value)
        return ""
    if item.get("StringValue") is not None:
        return item["StringValue"]
    if item.get("NumericValue") is not None:
        return item["NumericValue"]
    return "" if value is None else str(value)


def parse_spectrum_section(section: dict) -> List[dict]:
    """Group a PUG-View section's Information items into spectra by ReferenceNumber."""
    groups: Dict[int, Dict[str, Any]] = {}
    order: List[int] = []
    for item in section.get("Information", []) or []:
        ref = item.get("ReferenceNumber", 0)
        name = item.get("Name") or "field"
        if ref not in groups:
            groups[ref] = {}
            order.append(ref)
        groups[ref][name] = _extract_information_value(item)
    return [{"reference_number": ref, "data": groups[ref]} for ref in order]


def _collect_data_sections(sections: Optional[List[dict]]) -> List[dict]:
    """Collect all descendant sections that carry Information items."""
    out: List[dict] = []
    for section in sections or []:
        if section.get("Information"):
            out.append(section)
        out.extend(_collect_data_sections(section.get("Section", [])))
    return out


def _collect_sections(
    sections: Optional[List[dict]],
    target: Optional[str],
    raw_input: str,
    out: List[dict],
) -> List[dict]:
    """Find sections matching the requested spectrum type (case-insensitive)."""
    for section in sections or []:
        heading = section.get("TOCHeading", "")
        matched = bool(target and heading == target) or (
            not target and heading.strip().lower() == raw_input
        )
        if matched:
            out.append(section)
            out.extend(_collect_data_sections(section.get("Section", [])))
        else:
            _collect_sections(section.get("Section", []), target, raw_input, out)
    return out


def get_spectrum(cid: int, spectrum_type: str) -> dict:
    """Return parsed spectra of the requested type for a compound (PUG-View)."""
    data = fetch_pug_view(cid)
    key = spectrum_type.strip().lower()
    target = SPECTRUM_TYPE_ALIASES.get(key)
    sections = _collect_sections(data.get("Record", {}).get("Section", []), target, key, [])
    if not sections:
        raise ValueError(f"No {spectrum_type} spectra found for CID {cid}.")
    return {
        "cid": cid,
        "spectrum_type": spectrum_type,
        "sections": [
            {"heading": section.get("TOCHeading"), "spectra": parse_spectrum_section(section)}
            for section in sections
            if section.get("Information")
        ],
    }
