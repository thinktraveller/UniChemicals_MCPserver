# UniChemicals MCP Server

[![PyPI version](https://badge.fury.io/py/unichemicals-mcp-server.svg)](https://badge.fury.io/py/unichemicals-mcp-server)

[English Version](README.md)

## 🔬 项目简介

这是一个多数据库化学查询的 [MCP (Model Context Protocol)](https://github.com/modelcontextprotocol) 服务器，同时连接 **PubChem**（基于 `PubChemPy`）与 **CAS Common Chemistry**（官方 API，API key 鉴权）。

**它的作用是什么？**
这个服务器相当于 AI 助手（如 Claude, Cursor, Trae）与公共化学数据库之间的桥梁。通过集成该 MCP 服务器，你的 AI 助手将能自主搜索、提取和分析来自 PubChem（海量免费化学记录）与 CAS Common Chemistry（物质摘要、完整详情、性质与 molfile）的化学数据。

**为什么要使用它？**
与其手动在 PubChem 或 CAS 网站上搜索分子式、分子量、结构代码（SMILES/InChI）、同义词、3D 构象或 molfile，不如直接把任务交给 AI。

> **数据来源：** PubChem 数据实时来自 PubChem 官方 REST 服务（PUG REST / PUG-View）；CAS 数据来自 CAS Common Chemistry API（`https://commonchemistry.cas.org/api`）。本服务器不保存任何本地缓存或数据库。

---

## 🚀 安装与配置

无需繁琐的安装过程，你可以通过 `uvx` 直接运行此服务器。

### CAS Common Chemistry API key（`cas_*` 工具必需）

使用 `cas_*` 工具需要 CAS Common Chemistry API 令牌。请在启动服务器的目录下创建 `.env` 文件（或在环境中导出该变量）：

```env
CAS_COMMON_CHEMISTRY_API_KEY=your_api_key_here
```

模板见 `.env.example`。PubChem 工具（`pubchem_*`）不需要任何 key。

### MCP 客户端配置

在你的 MCP 客户端配置文件（如 Cherry Studio 的「MCP 服务器」导入，或 `claude_desktop_config.json`）中添加以下内容。也可直接使用现成文件 [`mcp-client-example.json`](mcp-client-example.json)：

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

- 将 `your_api_key_here` 替换为你的真实 CAS Common Chemistry API 令牌（与 `.env` 中 `CAS_COMMON_CHEMISTRY_API_KEY` 的值一致）。`cas_*` 工具会从该环境变量读取 key。
- `env` 段在 Cherry Studio 及大多数现代 MCP 客户端中受支持；若你的客户端不支持 `env`，请改在操作系统/用户环境变量中设置同名变量。
- 如果只需要 PubChem 工具（`pubchem_*`），可删除 `env` 段。

*提示：`--refresh` 参数确保每次启动客户端时，都会从 PyPI 获取并使用最新版本的服务器代码。*

---

## 🛠️ 可用工具列表 (API 参考)

本服务器提供 **47 个语义化工具**——36 个 `pubchem_*` 工具与 11 个 `cas_*` 工具，每个工具按 `{数据库}_{动作}_{实体}_by_{标识符}` 命名，数据来源（`pubchem` / `cas`）、动作（`search` / `get` / `resolve`）、实体与搜索依据一目了然。

### CAS Common Chemistry 工具（`cas_*`）

基于官方 CAS Common Chemistry API（`/search`、`/detail`、`/export`），使用 `X-Api-Key` 请求头鉴权。

#### 物质搜索（`cas_search_substance_by_*`）

所有搜索工具共用 `/search` 端点；均支持 `offset`（默认 0）与 `size`（1~100，默认 10）分页参数。搜索不区分大小写。

- `cas_search_substance_by_name`：按名称搜索，支持尾部通配符（如 `car*`）。
- `cas_search_substance_by_casrn`：按 CAS 登记号（带或不带连字符，如 `50-00-0`）。
- `cas_search_substance_by_smiles`：按 SMILES（canonical 或 isomeric）。
- `cas_search_substance_by_inchi`：按 InChI（带或不带 `InChI=` 前缀）。
- `cas_search_substance_by_inchikey`：按 InChIKey（自动补充 `InChIKey=` 前缀——实测该前缀必需）。

#### 物质详情（`cas_get_substance_by_*`）

- `cas_get_substance_by_casrn`：按 CAS 登记号获取完整详情（URI、名称、InChI/InChIKey、canonical SMILES、分子式/分子量、实验性质与引用、同义词、被替代 RN、SVG 结构图）。
- `cas_get_substance_by_uri`：按 API 返回的精确 `uri` 获取同样详情（如 `substance/pt/50000`）。

#### molfile 导出（`cas_get_molfile_by_*`）

- `cas_get_molfile_by_uri`：按 URI 直接导出 V2000 molfile 文本（`/export`）。
- `cas_get_molfile_by_casrn`：便捷封装——先经 `/detail` 解析 URI，再导出 molfile。

#### 便捷提取工具（`cas_get_*_by_casrn`）

- `cas_get_properties_by_casrn`：从 `/detail` 提取实验性质与性质引用。
- `cas_get_image_by_casrn`：从 `/detail` 提取结构图（SVG）。

> **数据政策：** CAS Common Chemistry 数据由 CAS（美国化学会）按自身条款提供，访问条件见 [CAS Common Chemistry 官网](https://www.cas.org/services/commonchemistry-api)。本服务器仅反映你的 key 可调用的 API 能力。

### 1. 化合物搜索 (`pubchem_search_compound_by_*`)
从 PubChem 数据库中检索经过标准化的化合物记录。
- **工具列表**:
  - `pubchem_search_compound_by_cid`
  - `pubchem_search_compound_by_name`
  - `pubchem_search_compound_by_smiles`
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

### 3. 生物测定搜索 (`pubchem_search_assay_by_aid`)
检索生物测定（生物活性）记录。
- **工具列表**:
  - `pubchem_search_assay_by_aid`

### 4. 属性批量获取 (`pubchem_get_property_by_*`)
无需下载完整的化合物记录，即可高效地批量获取特定的化学属性。
- **工具列表**:
  - `pubchem_get_property_by_cid`, `name`, `smiles`, `inchi`, `inchikey`, `formula`
  - `pubchem_get_property_by_cids`（批量：传入 CID 列表）
- **参数说明**:
  - `properties`: 需要获取的属性列表 (例如：`['MolecularFormula', 'MolecularWeight', 'InChI', 'CanonicalSMILES', 'IsomericSMILES', 'XLogP']`)。
  - `identifier`: 搜索关键词。
  - `cids`（批量工具）: CID 列表（单次不超过 100 个）。

### 5. 同义词与别名 (`pubchem_get_synonym_by_*`)
获取特定化学物质的所有已知别名、系统命名和商品名。
- **工具列表**:
  - `pubchem_get_synonym_by_cid`, `name`, `smiles`, `inchi`, `inchikey`, `formula`

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
uv run unichemicals-mcp-server
```

## 📜 许可证 (License)

本项目采用 **AGPL-3.0 许可证** 并附加了 **商业使用限制 (Commercial Use Restriction)** 条款。

- **传染性 (Copyleft)：** AGPL-3.0 具有传染性——任何基于本项目的衍生作品或网络服务，都必须以相同许可证条款开源。
- **商业使用：** 任何商业用途都必须从作者/版权所有者处获得单独的商业许可；未经授权，禁止商用。

详情请参阅 [LICENSE](LICENSE) 文件。

## 🙏 致谢 (Acknowledgments)

UniChemicals MCP Server 是一个多数据库化学查询服务，数据源包括 **PubChem** 与 **CAS Common Chemistry**。其中 PubChem 数据源基于 [mcs07](https://github.com/mcs07) 开发的优秀 Python 库 **[PubChemPy](https://github.com/mcs07/PubChemPy)** 接入，它是本项目依赖的底层库之一。我们向 PubChemPy 的原作者及所有贡献者表示最诚挚的感谢，感谢他们为访问 PubChem PUG REST API 提供了如此稳定、便捷的基础工具。
