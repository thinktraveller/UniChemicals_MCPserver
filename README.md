# UniChemicals MCP Server

[![PyPI version](https://badge.fury.io/py/unichemicals-mcp-server.svg)](https://badge.fury.io/py/unichemicals-mcp-server)

[中文版 (Chinese Version)](README_zh.md)

## 🔬 Introduction

An [MCP (Model Context Protocol)](https://github.com/modelcontextprotocol) server for multi-database chemistry queries, combining **PubChem** (via `PubChemPy`) and **CAS Common Chemistry** (official API, API-key authenticated).

**What does it do?**
This server acts as a bridge between AI assistants (like Claude, Cursor, Trae) and public chemistry databases. By integrating this MCP server, your AI assistant gains the ability to autonomously search, retrieve, and analyze chemical compounds from PubChem (millions of freely accessible records) and CAS Common Chemistry (substance summaries, full details, properties and molfiles) directly within your chat or development environment.

**Why use it?**
Instead of manually browsing PubChem or CAS websites to find molecular formulas, weights, structures (SMILES/InChI), synonyms, 3D conformers or molfiles, you can simply ask your AI assistant.

> **Data sources:** PubChem data is fetched in real time from PubChem's official REST services (PUG REST / PUG-View); CAS data is fetched from the CAS Common Chemistry API (`https://commonchemistry.cas.org/api`). This server keeps no local cache or database.

---

## 🚀 Installation & Configuration

You can use this server directly via `uvx` without manual installation.

### CAS Common Chemistry API key (required for `cas_*` tools)

To use the `cas_*` tools you need a CAS Common Chemistry API token. Create a `.env` file in the directory you launch the server from (or export the variable in your environment):

```env
CAS_COMMON_CHEMISTRY_API_KEY=your_api_key_here
```

See `.env.example` for the template. The PubChem tools (`pubchem_*`) do not require any key.

### MCP client configuration

Add the following to your MCP client configuration (e.g., Cherry Studio `MCP Servers` import, or `claude_desktop_config.json`). A ready-to-use file is provided at [`mcp-client-example.json`](mcp-client-example.json):

```json
{
  "mcpServers": {
    "unichemicals": {
      "command": "uvx",
      "args": [
        "--refresh",
        "unichemicals-mcp-server"
      ],
      "env": {
        "CAS_COMMON_CHEMISTRY_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

- Replace `your_api_key_here` with your real CAS Common Chemistry API token (the same value as `CAS_COMMON_CHEMISTRY_API_KEY` in `.env`). The `cas_*` tools read the key from this environment variable.
- The `env` block is supported by Cherry Studio and most modern MCP clients. If your client does not support `env`, set the same variable in your OS/user environment instead.
- Remove the `env` block if you only need the PubChem tools (`pubchem_*`).

*Note: The `--refresh` flag ensures you always pull the latest version from PyPI.*

---

## 🛠️ Available Tools (API Reference)

This server exposes **51 semantic tools** — 40 `pubchem_*` tools and 11 `cas_*` tools — each named as `{database}_{action}_{entity}_by_{identifier}` so the source database (`pubchem` / `cas`), the action (`search` / `get` / `resolve`), the entity and the search key are always explicit.

### CAS Common Chemistry tools (`cas_*`)

Powered by the official CAS Common Chemistry API (`/search`, `/detail`, `/export`), authenticated with `X-Api-Key`.

#### Search substances (`cas_search_substance_by_*`)

All search tools share the `/search` endpoint; each accepts `offset` (default 0) and `size` (1–100, default 10) for pagination. Searches are case-insensitive.

- `cas_search_substance_by_name`: name search, supports a trailing wildcard (e.g. `car*`).
- `cas_search_substance_by_casrn`: CAS Registry Number (with or without dashes, e.g. `50-00-0`).
- `cas_search_substance_by_smiles`: SMILES (canonical or isomeric).
- `cas_search_substance_by_inchi`: InChI (with or without the `InChI=` prefix).
- `cas_search_substance_by_inchikey`: InChIKey (the `InChIKey=` prefix is added automatically — required by the API in practice).

#### Substance details (`cas_get_substance_by_*`)

- `cas_get_substance_by_casrn`: full details by CAS RN (URI, names, InChI/InChIKey, canonical SMILES, molecular formula/mass, experimental properties + citations, synonyms, replaced RNs, SVG images).
- `cas_get_substance_by_uri`: same details by the exact `uri` returned by the API (e.g. `substance/pt/50000`).

#### Molfile export (`cas_get_molfile_by_*`)

- `cas_get_molfile_by_uri`: V2000 molfile text by URI (`/export`).
- `cas_get_molfile_by_casrn`: convenience — resolves the URI via `/detail` first, then exports the molfile.

#### Convenience extractors (`cas_get_*_by_casrn`)

- `cas_get_properties_by_casrn`: experimental properties and property citations extracted from `/detail`.
- `cas_get_image_by_casrn`: structure images (SVG) extracted from `/detail`.

> **Data policy:** CAS Common Chemistry data is provided by CAS (American Chemical Society) under its own terms; see the [CAS Common Chemistry website](https://www.cas.org/services/commonchemistry-api) for access conditions. This server only reflects API capabilities available with your key.

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
  - `pubchem_search_compound_by_cids` (batch: pass a list of CIDs)
- **Arguments**:
  - `identifier`: The search query (int for cid, str for others).
  - `searchtype` (Optional): Advanced search type (`substructure`, `superstructure`, `similarity`).
  - `cids` (for the batch tool): A list of CIDs (at most 100 per request).

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
  - `pubchem_get_property_by_cids` (batch: pass a list of CIDs)
- **Arguments**:
  - `properties`: A list of desired properties (e.g., `['MolecularFormula', 'MolecularWeight', 'InChI', 'CanonicalSMILES', 'IsomericSMILES', 'XLogP']`).
  - `identifier`: The search query.
  - `cids` (for the batch tool): A list of CIDs (at most 100 per request).

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

### 7. 3D Structure & Descriptors (`pubchem_get_*_by_cid`)
Retrieve 3D conformers, computed descriptors, and atom/bond topology for a single compound.
- **Tools**:
  - `pubchem_get_conformer_by_cid`: 3D coordinates (note: not every compound has 3D data).
  - `pubchem_get_descriptor_by_cid`: computed descriptors (MolecularWeight, XLogP, TPSA, HBondDonorCount, etc.); accepts an optional `properties` list, defaults to the standard set.
  - `pubchem_get_structure_by_cid`: atom/bond topology (elements, coordinates, bond orders).
  - `pubchem_get_spectrum_by_cid`: spectral data (1H/13C NMR, GC-MS, MS-MS, LC-MS, IR, FTIR, ATR-IR, UV, Raman) via PubChem PUG-View; not every compound has spectra.

---

## 💻 Local Development

If you want to contribute or run from source:

```bash
# Clone the repository
git clone https://github.com/yourusername/pubchem-mcp-server.git
cd pubchem-mcp-server

# Build and run using uv
uv build
uv run unichemicals-mcp-server
```

## 📜 License

This project is licensed under the **AGPL-3.0 License** with an additional **Commercial Use Restriction** clause.

- **Copyleft:** the AGPL-3.0 license is infectious — any derivative work or networked service based on this project must be released under the same license terms.
- **Commercial use:** any commercial use requires a separate commercial license from the author. Without such authorization, commercial use is prohibited.

See the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

This project is built upon and serves as an MCP wrapper for the excellent **[PubChemPy](https://github.com/mcs07/PubChemPy)** library created by [mcs07](https://github.com/mcs07). We extend our deepest gratitude to the original author and contributors of PubChemPy for providing such a robust Python interface to the PubChem PUG REST API.
