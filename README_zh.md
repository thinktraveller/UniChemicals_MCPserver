# PubChem MCP Server

[![PyPI version](https://badge.fury.io/py/pubchempy-mcp-server.svg)](https://badge.fury.io/py/pubchempy-mcp-server)

[English Version](README.md)

## 🔬 项目简介

这是一个基于 `PubChemPy` 构建的 [MCP (Model Context Protocol)](https://github.com/modelcontextprotocol) 服务器，专为连接 PubChem 数据库（全球最大的免费化学信息数据库）而设计。

**它的作用是什么？**
这个服务器相当于 AI 助手（如 Claude, Cursor, Trae）与 PubChem 数据库之间的桥梁。通过集成该 MCP 服务器，你的 AI 助手将获得自主搜索、提取和分析数以百万计的化学化合物、物质和生物测定数据的能力，这一切都可以在你的对话框或开发环境中直接完成。

**为什么要使用它？**
与其手动在 PubChem 网站上搜索分子式、分子量、结构代码（SMILES/InChI）、同义词或 3D 构象，不如直接把任务交给 AI。AI 可以调用这里提供的工具来查询数据库，并为多种化学物质批量获取属性。

> **数据来源：** 所有数据均实时来自 PubChem 官方 REST 服务（PUG REST / PUG-View）。本服务器不保存任何本地缓存或数据库。

---

## 🚀 安装与配置

无需繁琐的安装过程，你可以通过 `uvx` 直接运行此服务器。

在你的 MCP 客户端配置文件（如 `claude_desktop_config.json`）中添加以下内容：

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

*提示：`--refresh` 参数确保每次启动客户端时，都会从 PyPI 获取并使用最新版本的服务器代码。*

---

## 🛠️ 可用工具列表 (API 参考)

本服务器提供 **40 个语义化工具**，每个工具按 `pubchem_{动作}_{实体}_by_{标识符}` 命名，数据来源（`pubchem`）、动作（`search` / `get` / `resolve`）、实体与搜索依据一目了然。

### 1. 化合物搜索 (`pubchem_search_compound_by_*`)
从 PubChem 数据库中检索经过标准化的化合物记录。
- **工具列表**:
  - `pubchem_search_compound_by_cid`
  - `pubchem_search_compound_by_name`
  - `pubchem_search_compound_by_smiles`
  - `pubchem_search_compound_by_sdf`
  - `pubchem_search_compound_by_inchi`
  - `pubchem_search_compound_by_inchikey`
  - `pubchem_search_compound_by_formula`
  - `pubchem_search_compound_by_cids`（批量：传入 CID 列表）
- **参数说明**:
  - `identifier`: 搜索关键词（cid 为整数，其余为字符串）。
  - `searchtype` (可选): 高级搜索类型 (`substructure` 子结构, `superstructure` 超结构, `similarity` 相似度)。
  - `cids`（批量工具）: CID 列表（单次不超过 100 个）。

### 2. 物质搜索 (`pubchem_search_substance_by_*`)
检索最初提交给 PubChem 的未经标准化的原始物质记录。
- **工具列表**:
  - `pubchem_search_substance_by_sid`
  - `pubchem_search_substance_by_name`
  - `pubchem_search_substance_by_sourceid` (需要 `sourceid` 和 `source_name`)

### 3. 生物测定搜索 (`pubchem_search_assay_by_aid`)
检索生物测定（生物活性）记录。
- **工具列表**:
  - `pubchem_search_assay_by_aid`

### 4. 属性批量获取 (`pubchem_get_property_by_*`)
无需下载完整的化合物记录，即可高效地批量获取特定的化学属性。
- **工具列表**:
  - `pubchem_get_property_by_cid`, `name`, `smiles`, `sdf`, `inchi`, `inchikey`, `formula`
  - `pubchem_get_property_by_cids`（批量：传入 CID 列表）
- **参数说明**:
  - `properties`: 需要获取的属性列表 (例如：`['MolecularFormula', 'MolecularWeight', 'InChI', 'CanonicalSMILES', 'IsomericSMILES', 'XLogP']`)。
  - `identifier`: 搜索关键词。
  - `cids`（批量工具）: CID 列表（单次不超过 100 个）。

### 5. 同义词与别名 (`pubchem_get_synonym_by_*`)
获取特定化学物质的所有已知别名、系统命名和商品名。
- **工具列表**:
  - `pubchem_get_synonym_by_cid`, `name`, `smiles`, `sdf`, `inchi`, `inchikey`, `formula`

### 6. 标识符转换 (`pubchem_resolve_*_by_*`)
在不同的化学标识符之间进行转换（例如，通过名称或 SMILES 查找对应的 CID）。
- **工具列表**:
  - `pubchem_resolve_cid_by_name`, `smiles`, `inchi`, `inchikey`, `formula`
  - `pubchem_resolve_sid_by_cid`, `name`
  - `pubchem_resolve_aid_by_cid`, `name`

### 7. 3D 结构与描述符 (`pubchem_get_*_by_cid`)
获取单个化合物的 3D 构象、计算描述符与原子/键拓扑。
- **工具列表**:
  - `pubchem_get_conformer_by_cid`: 3D 坐标（注意：并非所有化合物都有 3D 数据）。
  - `pubchem_get_descriptor_by_cid`: 计算描述符（MolecularWeight、XLogP、TPSA、HBondDonorCount 等）；支持可选 `properties` 列表，默认返回标准集。
  - `pubchem_get_structure_by_cid`: 原子/键拓扑（元素、坐标、键级）。
  - `pubchem_get_spectrum_by_cid`: 光谱数据（1H/13C NMR、GC-MS、MS-MS、LC-MS、IR、FTIR、ATR-IR、UV、Raman），经 PubChem PUG-View 获取；并非所有化合物都有光谱。

---

## 💻 本地开发

如果你希望进行二次开发或从源码运行：

```bash
# 克隆仓库
git clone https://github.com/yourusername/pubchem-mcp-server.git
cd pubchem-mcp-server

# 使用 uv 构建并运行
uv build
uv run pubchempy-mcp-server
```

## 📜 许可证 (License)

本项目采用 **AGPL-3.0 许可证** 并附加了 **商业使用限制 (Commercial Use Restriction)** 条款。

- **传染性 (Copyleft)：** AGPL-3.0 具有传染性——任何基于本项目的衍生作品或网络服务，都必须以相同许可证条款开源。
- **商业使用：** 任何商业用途都必须从作者/版权所有者处获得单独的商业许可；未经授权，禁止商用。

详情请参阅 [LICENSE](LICENSE) 文件。

## 🙏 致谢 (Acknowledgments)

本项目是基于 [mcs07](https://github.com/mcs07) 开发的优秀 Python 库 **[PubChemPy](https://github.com/mcs07/PubChemPy)** 构建的 MCP 封装服务。我们向 PubChemPy 的原作者及所有贡献者表示最诚挚的感谢，感谢他们为访问 PubChem PUG REST API 提供了如此稳定、便捷的基础工具。
