# PubChem MCP Server

[![PyPI version](https://badge.fury.io/py/pubchempy-mcp-server.svg)](https://badge.fury.io/py/pubchempy-mcp-server)

[English Version](README.md)

## 🔬 项目简介

这是一个基于 `PubChemPy` 构建的 [MCP (Model Context Protocol)](https://github.com/modelcontextprotocol) 服务器，专为连接 PubChem 数据库（全球最大的免费化学信息数据库）而设计。

**它的作用是什么？**
这个服务器相当于 AI 助手（如 Claude, Cursor, Trae）与 PubChem 数据库之间的桥梁。通过集成该 MCP 服务器，你的 AI 助手将获得自主搜索、提取和分析数以百万计的化学化合物、物质和生物测定数据的能力，这一切都可以在你的对话框或开发环境中直接完成。

**为什么要使用它？**
与其手动在 PubChem 网站上搜索分子式、分子量、结构代码（SMILES/InChI），或是手动下载 3D SDF 文件，不如直接把任务交给 AI。AI 可以调用这里提供的工具来查询数据库、批量获取多种化学物质的属性，甚至可以直接将结构文件下载到你的本地电脑供进一步研究。

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

为了确保 AI 能够精确执行任务，本服务器将功能按照主要作用和标识符命名空间拆分成了 40 多个独立的工具。

### 1. 化合物搜索 (`get_compounds_by_*`)
从 PubChem 数据库中检索经过标准化的化合物记录。
- **工具列表**: 
  - `get_compounds_by_cid`
  - `get_compounds_by_name`
  - `get_compounds_by_smiles`
  - `get_compounds_by_sdf`
  - `get_compounds_by_inchi`
  - `get_compounds_by_inchikey`
  - `get_compounds_by_formula`
- **参数说明**: 
  - `identifier`: 搜索关键词（cid 为整数，其余为字符串）。
  - `searchtype` (可选): 高级搜索类型 (`substructure` 子结构, `superstructure` 超结构, `similarity` 相似度)。

### 2. 物质搜索 (`get_substances_by_*`)
检索最初提交给 PubChem 的未经标准化的原始物质记录。
- **工具列表**: 
  - `get_substances_by_sid`
  - `get_substances_by_name`
  - `get_substances_by_sourceid` (需要 `sourceid` 和 `source_name`)

### 3. 生物测定搜索 (`get_assays_by_*`)
检索生物测定（生物活性）记录。
- **工具列表**: 
  - `get_assays_by_aid`

### 4. 属性批量获取 (`get_properties_by_*`)
无需下载完整的化合物记录，即可高效地批量获取特定的化学属性。
- **工具列表**: 
  - `get_properties_by_cid`, `name`, `smiles`, `sdf`, `inchi`, `inchikey`, `formula`
- **参数说明**: 
  - `properties`: 需要获取的属性列表 (例如：`['MolecularFormula', 'MolecularWeight', 'InChI', 'CanonicalSMILES', 'IsomericSMILES', 'XLogP']`)。
  - `identifier`: 搜索关键词。

### 5. 同义词与别名 (`get_synonyms_by_*`)
获取特定化学物质的所有已知别名、系统命名和商品名。
- **工具列表**: 
  - `get_synonyms_by_cid`, `name`, `smiles`, `sdf`, `inchi`, `inchikey`, `formula`

### 6. 标识符转换 
在不同的化学标识符之间进行转换（例如，通过名称或 SMILES 查找对应的 CID）。
- **工具列表**:
  - `get_cids_by_name`, `smiles`, `inchi`, `inchikey`, `formula`
  - `get_sids_by_cid`, `name`
  - `get_aids_by_cid`, `name`

### 7. 文件下载 (`download_by_*`)
将化学结构文件或数据表格直接下载到本地文件系统中。
- **工具列表**: 
  - `download_by_cid`, `name`, `smiles`, `sdf`, `inchi`, `inchikey`, `formula`
- **参数说明**:
  - `identifier`: 搜索关键词。
  - `outformat`: 需要下载的文件格式 (`XML`, `JSON`, `SDF`, `CSV`, `PNG`, `TXT`)。
  - `path`: 保存文件的绝对路径。
  - `overwrite` (可选): 如果文件已存在，是否覆盖。

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
任何商业用途均需要从作者/版权所有者处获得单独的商业许可。详情请参阅 [LICENSE](LICENSE) 文件。

## 🙏 致谢 (Acknowledgments)

本项目是基于 [mcs07](https://github.com/mcs07) 开发的优秀 Python 库 **[PubChemPy](https://github.com/mcs07/PubChemPy)** 构建的 MCP 封装服务。我们向 PubChemPy 的原作者及所有贡献者表示最诚挚的感谢，感谢他们为访问 PubChem PUG REST API 提供了如此稳定、便捷的基础工具。