# pubchempy-mcp-server 学习笔记

## 项目概览
- **一句话描述**：基于 PubChemPy 构建的 MCP (Model Context Protocol) 服务器，把 PubChem 化学数据库的查询能力包装成 40+ 个 AI 助手可调用的工具（搜索化合物、批量获取属性、下载结构文件等）。
- **技术栈**：Python >=3.10 / FastMCP（`mcp[cli]>=1.0.0`）/ PubChemPy（`pubchempy>=1.0.5`）/ pandas / hatchling 构建。
- **项目类型**：MCP 服务器（Python 包，提供 `pubchempy-mcp-server` CLI 入口，通过 stdio 与 AI 客户端通信）。

## 架构与模块

### server.py（唯一代码模块）
- **职责**：使用 `FastMCP` 定义并注册全部 MCP 工具；`main()` 调用 `mcp.run()` 启动服务。
- **关键文件**：`src/pubchempy_mcpserver/server.py`（约 13KB，无其他代码文件）。
- **对外接口**：`@mcp.tool()` 注册的工具函数；`__init__.py` 为空。

### 工具分组（按功能和标识符命名空间拆分）
- **搜索类**：`get_compounds_by_*`（化合物）、`get_substances_by_*`（原始物质）、`get_assays_by_aid`（生物测定）。
- **属性批量获取**：`get_properties_by_*`，只取指定属性（分子式、分子量、SMILES、XLogP 等），避免下载整条记录。
- **同义词**：`get_synonyms_by_*`。
- **标识符转换**：`get_cids_by_*`、`get_sids_by_*`、`get_aids_by_*`。
- **文件下载**：`download_by_*`，通过 `pcp.download` 把 XML/JSON/SDF/CSV/PNG/TXT 保存到本地文件系统。

### 辅助函数 `_safe_execute`
- **职责**：统一执行 PubChemPy 调用 → 序列化为 JSON 字符串 → 捕获并返回异常信息（不向调用方抛异常）。
- **序列化规则**：结果若是 `Compound`/`Substance`/`Assay` 对象（有 `to_dict()`）或对象列表，转成 dict 再 `json.dumps`；否则直接序列化。

## 核心数据流

```
AI 客户端（Claude/Cursor/Trae）
        │  MCP 协议（stdio）
        ▼
FastMCP 路由到对应 tool 函数
        │
        ▼
_safe_execute 调用 pubchempy 函数（get_compounds / get_properties / download ...）
        │
        ▼
PubChemPy 包内部发起 HTTP GET 请求 → PubChem 官方 PUG REST API
        │
        ▼
PubChem 数据库返回 JSON/XML/SDF/CSV/PNG/TXT
        │
        ▼
PubChemPy 解析为 Compound/Substance/Assay 对象 → to_dict()
        │
        ▼
JSON 字符串返回给 AI 客户端
```

## 设计说明

### 1. 接入 PubChem 的方式：包 + 官方 REST API（非爬虫）
这是用户最关心的问题，结论是**两层结构**：
- **项目自身没有任何 HTTP / 网络爬虫代码**：`server.py` 里只有对 `pcp.*` 函数的调用，不直接写 `requests` 或解析 HTML。
- **真正的网络层在 `pubchempy` 包里**：PubChemPy 是 PubChem 官方 PUG REST API（`https://pubchem.ncbi.nlm.nih.gov/rest/pug/...`）的 Python 封装，负责发 HTTP 请求并把 JSON/XML/SDF 解析成 Python 对象。
- **不是爬虫**：没有网页抓取、无 HTML 解析，使用的是官方提供的结构化 REST 端点。
- 证据：`pyproject.toml` 依赖 `pubchempy>=1.0.5`；`README_zh.md` 致谢明确写道「为访问 PubChem PUG REST API 提供了如此稳定、便捷的基础工具」。

### 2. 为什么所有工具都返回字符串 JSON
MCP 工具输出必须是可序列化的；统一返回 `str` 并让 AI 自行解析，保证协议兼容且结果可读。

### 3. 错误处理策略：不抛异常，返回 "Error: ..."
`_safe_execute` 把异常捕获后以字符串返回，AI 客户端能直接看到错误信息并自我修正（例如换个查询写法重试），而不是让整个工具调用崩溃。

### 4. `sourceid` 命名空间拼接技巧
`get_substances_by_sourceid` 把 `source_name` 拼进命名空间字符串 `sourceid/{source_name}` 再传给 PubChemPy，因为 PUG API 的 substance 命名空间支持这种复合写法。

### 5. `searchtype` 透传高级搜索
化合物类工具可传 `substructure`（子结构）、`superstructure`（超结构）、`similarity`（相似度）三种高级搜索类型，直接透传给 PubChemPy。

### ⚠️ 已知问题：打包配置与源码目录名不一致
`pyproject.toml` 中：
- `[project.scripts]` 入口写的是 `pubchem_mcp_server.server:main`
- `[tool.hatch.build.targets.wheel] packages = ["src/pubchem_mcp_server"]`

但实际源码目录是 `src/pubchempy_mcpserver/`（`pubchempy` + `mcpserver`，无下划线），git 中跟踪的也只有这个目录。因此按当前配置构建 wheel 大概率会失败或产不出包含代码的包；本地运行若直接从源码目录导入则不受影响（可运行 `python src/pubchempy_mcpserver/server.py` 验证）。这属于配置遗留问题，需在二次开发时修正为与实际目录一致。

## Q&A 记录

### PubChem 接入方式

**Q：** 这个项目是如何实现的？通过什么方式接入 PubChem 数据库（API 接口？包？爬虫？）

**A：** 实现上是一个薄封装：MCP 工具层直接委托给 PubChemPy 包，由 PubChemPy 调用 PubChem 官方 PUG REST API。
- 具体链路：AI 客户端 → FastMCP 工具 → `_safe_execute` → `pcp.get_compounds`/`get_properties`/`download` → PubChemPy 发 HTTP GET 到 PUG REST API → 解析结果 → JSON 返回。
- 答案是「**包**（PubChemPy）+ 底层「**官方 API 接口**（PUG REST API）」，不是爬虫。
- 当前工作区未安装 `pubchempy`，本文档未实际运行项目；接入机制结论基于代码结构 + README 明示（README 中明确写了 PUG REST API，属确定信息）。

## 二次开发备忘

（暂无；若后续要修正打包配置或扩展工具，可在此追加记录）
