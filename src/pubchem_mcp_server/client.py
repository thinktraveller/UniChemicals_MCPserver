"""PubChem data access layer.

Wraps PubChemPy (PUG REST) calls so MCP tools never talk to PubChemPy
directly. PubChemPy uses ``urllib`` internally without an explicit timeout,
so a default socket timeout is applied process-wide to avoid hanging requests.
"""

import socket
from typing import Any, List, Optional

import pubchempy as pcp

# PubChem PUG REST request timeout (seconds).
REQUEST_TIMEOUT = 30
socket.setdefaulttimeout(REQUEST_TIMEOUT)


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

