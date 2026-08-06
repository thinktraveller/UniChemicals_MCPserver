# PubChem MCP Server

[![PyPI version](https://badge.fury.io/py/pubchempy-mcp-server.svg)](https://badge.fury.io/py/pubchempy-mcp-server)

[中文版 (Chinese Version)](README_zh.md)

## 🔬 Introduction

An [MCP (Model Context Protocol)](https://github.com/modelcontextprotocol) server for the PubChem database, powered by `PubChemPy`.

**What does it do?**
This server acts as a bridge between AI assistants (like Claude, Cursor, Trae) and the PubChem database, which is the world's largest collection of freely accessible chemical information. By integrating this MCP server, your AI assistant gains the ability to autonomously search, retrieve, and analyze millions of chemical compounds, substances, and bioassays directly within your chat or development environment.

**Why use it?**
Instead of manually browsing the PubChem website to find molecular formulas, weights, structures (SMILES/InChI), synonyms or 3D conformers, you can simply ask your AI assistant. The AI can use the provided tools to query the database and batch retrieve properties for multiple chemicals.

> **Data source:** all data is fetched in real time from PubChem's official REST services (PUG REST / PUG-View). This server keeps no local cache or database.

---

## 🚀 Installation & Configuration

You can use this server directly via `uvx` without manual installation.

Add the following to your MCP client configuration (e.g., `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "pubchempy_server": {
      "command": "uvx",
      "args": [
        "--refresh",
        "pubchempy-mcp-server"
      ]
    }
  }
}
```

*Note: The `--refresh` flag ensures you always pull the latest version from PyPI.*

---

## 🛠️ Available Tools (API Reference)

This server exposes **34 semantic tools**, each named as `pubchem_{action}_{entity}_by_{identifier}` so the source database (`pubchem`), the action (`search` / `get` / `resolve`), the entity and the search key are always explicit.

### 1. Compound Search (`pubchem_search_compound_by_*`)
Retrieve standardized compound records from the PubChem database.
- **Tools**:
  - `pubchem_search_compound_by_cid`
  - `pubchem_search_compound_by_name`
  - `pubchem_search_compound_by_smiles`
  - `pubchem_search_compound_by_sdf`
  - `pubchem_search_compound_by_inchi`
  - `pubchem_search_compound_by_inchikey`
  - `pubchem_search_compound_by_formula`
- **Arguments**:
  - `identifier`: The search query (int for cid, str for others).
  - `searchtype` (Optional): Advanced search type (`substructure`, `superstructure`, `similarity`).

### 2. Substance Search (`pubchem_search_substance_by_*`)
Retrieve raw, unstandardized substance records as originally deposited to PubChem.
- **Tools**:
  - `pubchem_search_substance_by_sid`
  - `pubchem_search_substance_by_name`
  - `pubchem_search_substance_by_sourceid` (requires `sourceid` and `source_name`)

### 3. Assay Search (`pubchem_search_assay_by_aid`)
Retrieve bioassay (biological activity) records.
- **Tools**:
  - `pubchem_search_assay_by_aid`

### 4. Properties Retrieval (`pubchem_get_property_by_*`)
Efficiently retrieve specific chemical properties in batch without downloading the entire compound record.
- **Tools**:
  - `pubchem_get_property_by_cid`, `name`, `smiles`, `sdf`, `inchi`, `inchikey`, `formula`
- **Arguments**:
  - `properties`: A list of desired properties (e.g., `['MolecularFormula', 'MolecularWeight', 'InChI', 'CanonicalSMILES', 'IsomericSMILES', 'XLogP']`).
  - `identifier`: The search query.

### 5. Synonyms & Aliases (`pubchem_get_synonym_by_*`)
Fetch all known aliases, systematic names, and trade names for a given chemical.
- **Tools**:
  - `pubchem_get_synonym_by_cid`, `name`, `smiles`, `sdf`, `inchi`, `inchikey`, `formula`

### 6. Identifier Resolution (`pubchem_resolve_*_by_*`)
Convert between different chemical identifiers (e.g., finding the CID for a specific name or SMILES).
- **Tools**:
  - `pubchem_resolve_cid_by_name`, `smiles`, `inchi`, `inchikey`, `formula`
  - `pubchem_resolve_sid_by_cid`, `name`
  - `pubchem_resolve_aid_by_cid`, `name`

---

## 💻 Local Development

If you want to contribute or run from source:

```bash
# Clone the repository
git clone https://github.com/yourusername/pubchem-mcp-server.git
cd pubchem-mcp-server

# Build and run using uv
uv build
uv run pubchempy-mcp-server
```

## 📜 License

This project is licensed under the **AGPL-3.0 License** with an additional **Commercial Use Restriction** clause.

- **Copyleft:** the AGPL-3.0 license is infectious — any derivative work or networked service based on this project must be released under the same license terms.
- **Commercial use:** any commercial use requires a separate commercial license from the author. Without such authorization, commercial use is prohibited.

See the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

This project is built upon and serves as an MCP wrapper for the excellent **[PubChemPy](https://github.com/mcs07/PubChemPy)** library created by [mcs07](https://github.com/mcs07). We extend our deepest gratitude to the original author and contributors of PubChemPy for providing such a robust Python interface to the PubChem PUG REST API.
