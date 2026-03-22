# PubChem MCP Server

[![PyPI version](https://badge.fury.io/py/pubchempy-mcp-server.svg)](https://badge.fury.io/py/pubchempy-mcp-server)

[中文版 (Chinese Version)](README_zh.md)

## 🔬 Introduction

An [MCP (Model Context Protocol)](https://github.com/modelcontextprotocol) server for the PubChem database, powered by `PubChemPy`. 

**What does it do?**
This server acts as a bridge between AI assistants (like Claude, Cursor, Trae) and the PubChem database, which is the world's largest collection of freely accessible chemical information. By integrating this MCP server, your AI assistant gains the ability to autonomously search, retrieve, and analyze millions of chemical compounds, substances, and bioassays directly within your chat or development environment.

**Why use it?**
Instead of manually browsing the PubChem website to find molecular formulas, weights, structures (SMILES/InChI), or downloading 3D SDF files, you can simply ask your AI assistant. The AI can use the provided tools to query the database, batch retrieve properties for multiple chemicals, and even download structure files to your local machine for further research.

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

This server exposes over 40 distinct tools, carefully categorized by their primary function and identifier namespace to ensure precise AI execution.

### 1. Compound Search (`get_compounds_by_*`)
Retrieve standardized compound records from the PubChem database.
- **Tools**: 
  - `get_compounds_by_cid`
  - `get_compounds_by_name`
  - `get_compounds_by_smiles`
  - `get_compounds_by_sdf`
  - `get_compounds_by_inchi`
  - `get_compounds_by_inchikey`
  - `get_compounds_by_formula`
- **Arguments**: 
  - `identifier`: The search query (int for cid, str for others).
  - `searchtype` (Optional): Advanced search type (`substructure`, `superstructure`, `similarity`).

### 2. Substance Search (`get_substances_by_*`)
Retrieve raw, unstandardized substance records as originally deposited to PubChem.
- **Tools**: 
  - `get_substances_by_sid`
  - `get_substances_by_name`
  - `get_substances_by_sourceid` (requires `sourceid` and `source_name`)

### 3. Assay Search (`get_assays_by_*`)
Retrieve bioassay (biological activity) records.
- **Tools**: 
  - `get_assays_by_aid`

### 4. Properties Retrieval (`get_properties_by_*`)
Efficiently retrieve specific chemical properties in batch without downloading the entire compound record.
- **Tools**: 
  - `get_properties_by_cid`, `name`, `smiles`, `sdf`, `inchi`, `inchikey`, `formula`
- **Arguments**: 
  - `properties`: A list of desired properties (e.g., `['MolecularFormula', 'MolecularWeight', 'InChI', 'CanonicalSMILES', 'IsomericSMILES', 'XLogP']`).
  - `identifier`: The search query.

### 5. Synonyms & Aliases (`get_synonyms_by_*`)
Fetch all known aliases, systematic names, and trade names for a given chemical.
- **Tools**: 
  - `get_synonyms_by_cid`, `name`, `smiles`, `sdf`, `inchi`, `inchikey`, `formula`

### 6. Identifier Conversion 
Convert between different chemical identifiers (e.g., finding the CID for a specific name or SMILES).
- **Tools**:
  - `get_cids_by_name`, `smiles`, `inchi`, `inchikey`, `formula`
  - `get_sids_by_cid`, `name`
  - `get_aids_by_cid`, `name`

### 7. File Download (`download_by_*`)
Download chemical structure files or data tables directly to your local filesystem.
- **Tools**: 
  - `download_by_cid`, `name`, `smiles`, `sdf`, `inchi`, `inchikey`, `formula`
- **Arguments**:
  - `identifier`: The search query.
  - `outformat`: The desired file format (`XML`, `JSON`, `SDF`, `CSV`, `PNG`, `TXT`).
  - `path`: The absolute path where the file should be saved.
  - `overwrite` (Optional): Whether to overwrite if the file already exists.

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

This project is dual-licensed under the **AGPL-3.0 License** with an additional **Commercial Use Restriction** clause. 
Any commercial use requires a separate commercial license from the author. See the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

This project is built upon and serves as an MCP wrapper for the excellent **[PubChemPy](https://github.com/mcs07/PubChemPy)** library created by [mcs07](https://github.com/mcs07). We extend our deepest gratitude to the original author and contributors of PubChemPy for providing such a robust Python interface to the PubChem PUG REST API.