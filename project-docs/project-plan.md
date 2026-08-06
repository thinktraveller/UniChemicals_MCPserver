# pubchempy-mcp-server 构建计划书

## 项目概述

- **项目目标**：对 pubchempy-mcp-server 进行源码整理与功能扩展，使其结构清晰、可正常打包发布、工具语义化命名，并覆盖更丰富的 PubChem 数据类型（3D 结构/光谱/描述符等）。完整目标与澄清过程见 `project-docs/goal.md`（QA-R001 ~ QA-R005）。
- **预期成果与核心功能**：
  - 修正打包配置，`uv build` 可成功构建，项目可公开发布到 PyPI；
  - 代码按模块拆分，消除 40+ 个高度重复的工具函数；
  - MCP 工具全部改为语义化命名：`{数据库}_{动作}_{实体}_by_{标识符}`（如 `pubchem_search_compound_by_cid`）；
  - 移除 6 个 `download_by_*` 下载工具；
  - 补充批量查询等现有工具族能力，新增 3D 结构（conformer）、描述符、原子/键结构、光谱等工具；
  - 通过 `uvx` 跑通远程 MCP 服务。
- **目标用户或使用场景**：需要通过 AI 助手（Claude/Cursor/Trae 等 MCP 客户端）查询 PubChem 化学数据的用户与开发者，以及从 PyPI 安装使用的社区用户。

## 可行性分析

- **技术可行性评估**：可行。项目本身是 PubChemPy 的 MCP 薄封装，改造主要是「修打包 + 拆模块 + 换命名 + 扩工具」四件事，均有成熟路径。PubChemPy 已确认支持 `record_type='3d'` 获取 3D 结构；光谱数据经 PUG-View API 的「Spectral Information」heading 获取（PubChemPy 本身不覆盖，需少量直连代码）。
- **主要依赖与第三方服务**：
  - `mcp[cli] >= 1.0.0`：FastMCP 服务框架（现依赖）；
  - `pubchempy >= 1.0.5`：PubChem PUG REST 封装（现依赖）；
  - `pandas >= 2.0.0`：数据处理（现依赖，工具内部序列化可能用到）；
  - `requests >= 2.31`：新增，用于 PUG-View 光谱等直连调用；
  - PubChem PUG REST / PUG-View：外部数据服务，无需 API Key，但有频率限制。
- **开发工作量估算**：中等。打包修正 0.5 天、模块重构 1~2 天、语义化命名与工具迁移 1 天、工具扩展（批量/3D/描述符/光谱）1~2 天、验证与发布 1 天；合计约 4~6 个工作日（时间不紧迫，可拆解执行）。
- **潜在风险与应对策略**：
  - 打包配置错误是当前阻塞项，必须先修复才能做后续 `uvx` 验证（应对：步骤 1 优先，独立验证）；
  - 部分化合物没有 3D 结构数据（PubChemPy 已知 issue #49），工具需返回明确错误信息而非崩溃；
  - 光谱数据经 PUG-View 返回结构复杂（Section/Information 多层嵌套），需在实现时按真实响应核对字段路径；
  - AGPL-3.0 + 商业使用限制属「附加条款」组合，PyPI 元数据只能声明主许可证，需在 README/LICENSE 中说明商用需单独授权（应对：步骤 4 同步文档）；
  - 语义化重命名会使旧工具名失效（用户已确认不需要保留别名），README 与示例需同步更新；
  - 运行时访问 PubChem 需要网络可达 `pubchem.ncbi.nlm.nih.gov`，国内网络可能超时（应对：README 说明重试/代理，代码对超时做友好错误返回）。

## 技术选型

- **编程语言与运行环境**：Python `>= 3.10`；开发与构建工具 `uv >= 0.4.7`（`uv build` / `uvx` / `uv publish`；若 `uv publish` 不可用则用 twine 替代）。
- **核心框架与库**：FastMCP（`mcp[cli] >= 1.0.0`）；PubChemPy（`pubchempy >= 1.0.5`）；`requests >= 2.31`（新增，PUG-View 直连）；`pandas >= 2.0.0`（现依赖）。
- **数据存储方案**：无本地数据库。所有数据实时来自 PubChem REST 服务；下载类工具已按目标移除。
- **部署与基础设施**：构建为 wheel 发布到 PyPI，用户通过 `uvx` 本地运行 MCP 服务（stdio 传输）；无服务端部署。

## 环境配置

### 硬件/系统要求
- 普通开发机即可；运行 MCP 服务与调用 PubChem API 需要网络连接。

### 开发环境搭建
- 项目目录已存在且为 Git 仓库（`D:\Demo\UniChemicals_MCPserver`），无需 `git init`。
- 安装 uv（Windows PowerShell）：
  ```powershell
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```
- 使用 uv 同步开发环境：
  ```powershell
  uv venv
  uv pip install -e ".[dev]"
  ```

### 依赖安装
```powershell
# 1. 首先尝试官方源
uv add requests>=2.31
uv sync

# 2. 若官方源下载失败或超时，使用清华镜像
uv pip install requests -i https://pypi.tuna.tsinghua.edu.cn/simple
```
备用镜像：阿里云 `https://mirrors.aliyun.com/pypi/simple`、中科大 `https://pypi.mirrors.ustc.edu.cn/simple`。

## 开发计划

### 步骤 1：修正打包配置并跑通 `uv build`

#### 目标说明
当前 `pyproject.toml` 的包路径写的是 `src/pubchem_mcp_server`、入口点是 `pubchem_mcp_server.server:main`，但实际源码目录是 `src/pubchempy_mcpserver`（拼写不一致），按现状构建 wheel 会失败。本步骤统一包名并确认可构建。

#### 具体操作
1. 统一包目录名（推荐以 `pyproject.toml` 为准，目录改为 `pubchem_mcp_server`）：
   ```powershell
   git mv src/pubchempy_mcpserver src/pubchem_mcp_server
   ```
2. 检查 `pyproject.toml` 保持一致性：
   ```toml
   [project.scripts]
   pubchempy-mcp-server = "pubchem_mcp_server.server:main"

   [tool.hatch.build.targets.wheel]
   packages = ["src/pubchem_mcp_server"]
   ```
3. 补全许可证元数据（主许可证声明 AGPL-3.0，附加商业限制写在 LICENSE 与 README，见步骤 4）：
   ```toml
   license = "AGPL-3.0-only"
   ```
4. 构建并查看产物：
   ```powershell
   uv build
   Get-ChildItem dist
   ```
5. 本地启动验证入口可运行：
   ```powershell
   uv run pubchempy-mcp-server
   ```
   （MCP 服务默认以 stdio 启动，启动后无报错即可 Ctrl+C 退出。）

#### 验证方法
- `uv build` 退出码为 0，`dist/` 下生成 `.whl` 与 `.tar.gz`；
- wheel 内容包含 `pubchem_mcp_server/server.py`（可用 `tar -tf` 或解压检查）；
- `uv run pubchempy-mcp-server` 能正常启动、无 ImportError。

#### 风险提示
- 目录改名后所有 import 路径需同步（当前仅 server.py 自身引用，风险低）；
- 旧构建缓存（`dist/`、`*.egg-info`）可能导致误判，先清理再构建；
- 若保留旧目录名更符合预期，可反向修改 `pyproject.toml`，两者择一，不得并存。

### 步骤 2：重构代码结构（模块化 + 工具工厂消除重复）

#### 目标说明
当前 40+ 个工具是复制粘贴模式，维护成本高。将单文件拆分为「入口 + 注册表 + 客户端 + 工具/工具工厂」，让同族工具由配置驱动自动生成。

#### 具体操作
1. 目标目录结构：
   ```
   src/pubchem_mcp_server/
   ├── __init__.py
   ├── server.py          # FastMCP 实例、main()、工具注册入口
   ├── registry.py        # 工具描述注册表 + 工厂函数
   ├── client.py          # 对 pubchempy / PUG-View 的调用封装（含超时、限速、User-Agent）
   └── utils.py           # _safe_execute 迁移：序列化、异常捕获、对象转 dict
   ```
2. `utils.py` 承接原 `_safe_execute`，统一处理「有 `to_dict()` 的对象/对象列表 → JSON 字符串，异常 → `Error: ...` 字符串」。
3. `registry.py` 用配置驱动生成工具，示例：
   ```python
   # registry.py
   SEARCH_NAMESPACES = ["cid", "name", "smiles", "sdf", "inchi", "inchikey", "formula"]

   def make_search_compound_tool(namespace: str):
       def tool(identifier, searchtype=None):
           return safe_execute(pcp.get_compounds, identifier, namespace, searchtype=searchtype)
       tool.__name__ = f"pubchem_search_compound_by_{namespace}"
       tool.__doc__ = f"Search standardized compound records by {namespace}."
       return tool

   def register_all(mcp):
       for ns in SEARCH_NAMESPACES:
           mcp.tool(name=f"pubchem_search_compound_by_{ns}")(make_search_compound_tool(ns))
   ```
   > 说明：FastMCP 的 `mcp.tool(name=...)` 支持显式指定工具名；不同工具的入参类型（`identifier: int` vs `str`）需在工厂中按 namespace 区分，确保 MCP 生成的参数 schema 正确。
4. `server.py` 只保留 FastMCP 实例、`register_all(mcp)` 调用与 `main()`。

#### 验证方法
- 启动后工具数量与重构前一致（40+），且每个工具描述/docstring 存在；
- 抽查各命名空间（cid/name/smiles/formula 等）调用返回结构一致；
- `uv run pubchempy-mcp-server` 无注册冲突或参数 schema 报错。

#### 风险提示
- 动态注册时 `tool.__name__` 与 FastMCP 内部名称不一致会导致工具名错乱，务必显式传 `name=`；
- 列表型入参（如批量 cid）与 `Optional[str]` 的 searchtype 需明确类型标注，避免 schema 生成错误；
- 重构期间不改变工具对外行为，先保证等价，再进入步骤 3 改名。

### 步骤 3：工具语义化命名

#### 目标说明
按 `{数据库}_{动作}_{实体}_by_{标识符}` 统一命名，如 `pubchem_search_compound_by_cid`；动作词表固定为 `search`（查记录）/ `get`（取属性/同义词/结构）/ `resolve`（标识符转换），为未来接入 ChEMBL、DrugBank 等其他数据库预留命名空间。

#### 具体操作
1. 新旧命名映射（在 `registry.py` 中直接以新名注册，删除旧函数）：

   | 旧名称 | 新名称 |
   |---|---|
   | `get_compounds_by_cid/name/smiles/sdf/inchi/inchikey/formula` | `pubchem_search_compound_by_{namespace}` |
   | `get_substances_by_sid/name` | `pubchem_search_substance_by_sid/name` |
   | `get_substances_by_sourceid` | `pubchem_search_substance_by_sourceid` |
   | `get_assays_by_aid` | `pubchem_search_assay_by_aid` |
   | `get_properties_by_{ns}` | `pubchem_get_property_by_{ns}` |
   | `get_synonyms_by_{ns}` | `pubchem_get_synonym_by_{ns}` |
   | `get_cids_by_{ns}` | `pubchem_resolve_cid_by_{ns}` |
   | `get_sids_by_cid/name` | `pubchem_resolve_sid_by_cid/name` |
   | `get_aids_by_cid/name` | `pubchem_resolve_aid_by_cid/name` |
2. 不保留旧名别名（用户已确认）；如未来需要兼容，可在 `registry.py` 里为旧名注册 `mcp.tool(name=旧名)` 转发，属于低成本扩展点。
3. 每个工具 docstring 按新语义重写，注明参数与返回。

#### 验证方法
- 启动后 `mcp` 工具列表全部符合 `pubchem_*` 前缀规范，无 `get_compounds_by_*` 等旧名残留；
- 每个工具至少完成一次真实调用冒烟（需网络），如 `pubchem_search_compound_by_cid(2244)` 返回阿司匹林 JSON。

#### 风险提示
- 已接入的 MCP 客户端若引用旧工具名会失效（已确认接受）；README 中的工具列表必须同步，否则用户按文档找不到工具；
- 命名冲突检查：`sourceid` 需要 `sourceid` + `source_name` 两个参数，工厂函数需特判。

### 步骤 4：移除下载工具并同步文档与许可证元数据

#### 目标说明
删除 6 个 `download_by_*` 工具，同步清理 README（中英文）、README_zh 的工具清单，并落实 AGPL-3.0 + 商业使用限制的元数据与说明。

#### 具体操作
1. 在 `registry.py` / `server.py` 中删除所有 `download_by_*` 注册与 `pcp.download` 调用。
2. 更新 `README.md` 与 `README_zh.md`：
   - 删除「文件下载」工具组及示例；
   - 工具列表全部替换为新语义化名称；
   - 补充说明：数据实时来自 PubChem 官方 REST 服务，无本地缓存。
3. 许可证落实（LICENSE 已是 AGPL-3.0 + Commercial Use Restriction，保持）：
   - `pyproject.toml` 声明主许可证 `license = "AGPL-3.0-only"`；
   - README 明确：任何商业使用需单独获得作者许可，联系仓库所有者。
4. 版本号提升（如 `0.1.1 → 0.2.0`，因涉及破坏性变更）。

#### 验证方法
- 工具列表无任何 `download` 相关工具；
- README/README_zh 全文检索不到 `download_by_` 或「文件下载」工具说明；
- `uv build` 仍成功；`pip show`/`metadata` 中 license 字段正确。

#### 风险提示
- 文档与代码不同步是发布后最常见投诉源，README 的中英文版本都必须改；
- `license` 字段只能表达 SPDX 主许可，附加商业限制无法在元数据表达，务必在 README/LICENSE 用自然语言写清「商用需授权」。

### 步骤 5：补充工具族与挖掘 PubChemPy 能力（批量查询、3D、描述符、原子键）

#### 目标说明
在不引入新依赖的前提下，把 PubChemPy 已具备但当前未暴露的能力做成工具：列表批量查询、3D 结构（`record_type='3d'`）、全量计算描述符、原子/键拓扑数据。

#### 具体操作
1. **批量查询**（PubChemPy 支持列表入参）：
   ```python
   # 新工具：pubchem_search_compound_by_cids / pubchem_get_property_by_cids 等
   pcp.get_compounds([2244, 2245, 2246], "cid")
   pcp.get_properties(["MolecularFormula", "MolecularWeight", "XLogP"], [2244, 2245], "cid")
   ```
2. **3D 结构**（官方文档确认 `record_type='3d'`）：
   ```python
   # 新工具：pubchem_get_conformer_by_cid
   pcp.get_compounds(2244, "cid", record_type="3d")
   ```
   返回对象含 3D 坐标的 atoms/conformer 数据，序列化为 JSON；`to_dict()` 中字段以实际返回为准。
3. **描述符**：`pubchem_get_descriptor_by_cid` 暴露 PubChem 计算属性全集（MolecularWeight、XLogP、TPSA、HBD、HBA、ExactMass、HeavyAtomCount 等），参数支持指定属性列表，默认返回常用集。
4. **原子/键拓扑**：`pubchem_get_structure_by_cid` 返回 `Compound.atoms`（元素、坐标）与 `Compound.bonds`（键级、连接关系）。
5. 同样按工厂模式生成各 namespace 变体，保持命名规范。

#### 验证方法
- 批量工具传入 3 个 CID 返回 3 条记录；
- `pubchem_get_conformer_by_cid(2244)` 返回含 3D 坐标的数据；对无 3D 数据的化合物（如部分大分子），返回 `Error: ...` 且不崩溃；
- 描述符工具返回字段与 PubChem 属性名一致。

#### 风险提示
- 部分化合物无 3D 数据（PubChemPy issue #49），工具描述中注明，错误信息需可读；
- 批量列表过大可能触发 PUG 请求限制或超时，建议单次不超过 100 个标识符并在 docstring 中说明；
- PubChem 官方建议请求频率 < 5 次/秒，`client.py` 可加简单限速或重试。

### 步骤 6：新增 PUG-View 直连能力（光谱等 PubChemPy 未覆盖的数据）

#### 目标说明
PubChemPy 不提供光谱功能。光谱数据存在于 PubChem 的 PUG-View 服务（「Spectral Information」heading），本步骤新增 `client.py` 的直连封装与光谱工具。

#### 具体操作
1. `client.py` 增加 PUG-View 调用封装：
   ```python
   import requests

   def fetch_pug_view(cid: int, heading: str = "Spectral Information") -> dict:
       url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/{cid}/JSON"
       resp = requests.get(url, params={"heading": heading},
                           headers={"User-Agent": "pubchempy-mcp-server/0.2"},
                           timeout=30)
       resp.raise_for_status()
       return resp.json()
   ```
2. 新工具 `pubchem_get_spectrum_by_cid(cid, spectrum_type)`：先取整段「Spectral Information」，再从返回 JSON 的 `Record.Section` 树中定位对应光谱类型（1H NMR / 13C NMR / IR / MS 等）的 `Information` 节点，提取数据文本/峰值表。
3. 解析函数放在 `client.py` 或 `utils.py`，对「无该类型光谱」返回明确 `Error: ...`。
4. 对 PUG-View 调用加 30s 超时与简单重试（如 503 时退避重试 2 次）。

#### 验证方法
- `pubchem_get_spectrum_by_cid(2244, "1H NMR")` 返回阿司匹林 1H NMR 数据；
- 对无光谱数据的化合物返回友好错误，服务不崩溃；
- 单元层面验证解析函数能处理嵌套 Section 结构。

#### 风险提示
- PUG-View 返回结构复杂（Section/Information 多层嵌套且字段名随数据类型变化），实现时必须用真实响应核对，不能凭猜测写死路径；
- 光谱类型命名以实际响应为准，docstring 中列出已验证的类型；
- `requests` 直连增加了对 PubChem 网络服务的直接依赖，README 需注明数据来源与频率限制。

### 步骤 7：端到端验证与 PyPI 发布

#### 目标说明
验证「`uv build` 成功 + 基于 `uvx` 的远程 MCP 服务跑通」这一成功标准，并完成 PyPI 公开发布。

#### 具体操作
1. 本地全量验证：
   ```powershell
   uv build
   uv run pubchempy-mcp-server
   ```
   用一个 MCP 客户端（Claude Desktop / Cursor / MCP Inspector）接入 `uv run` 启动的服务，确认工具列表与各工具调用正常。
2. 版本与元数据检查：`pyproject.toml` 版本号、README、LICENSE 就绪。
3. 发布到 PyPI（官方源优先）：
   ```powershell
   # 需要 PyPI 账号与 API Token（https://pypi.org/manage/account/token/）
   uv publish
   ```
   若 `uv publish` 不可用，回退 twine：
   ```powershell
   uv pip install twine
   twine upload dist/*
   ```
4. 远程验证（从 PyPI 拉取最新版）：
   ```powershell
   uvx --refresh pubchempy-mcp-server
   ```
   确认无本地源码依赖、工具列表与发布版一致。

#### 验证方法
- 全新环境（仅安装 uv）执行 `uvx --refresh pubchempy-mcp-server` 能启动 MCP 服务；
- MCP 客户端可列出全部新命名工具，`pubchem_search_compound_by_cid(2244)` 等真实调用成功返回；
- PyPI 页面显示正确版本、README 与许可证说明。

#### 风险提示
- PyPI 包名 `pubchempy-mcp-server` 若已被占用需先查重（`https://pypi.org/project/pubchempy-mcp-server/`）；
- 发布后立刻发现 bug 需要 bump 版本重发，建议发布前完整走一遍本地 + 客户端验证；
- 国内网络下 `uvx` 拉包失败时，配置镜像 `UV_DEFAULT_INDEX` 或 `PIP_INDEX_URL` 到清华源重试（官方源优先）。

## Q&A 记录

### 通用问题

**Q：** 为什么许可证最终选 AGPL-3.0 + 商业使用限制，而不是 PolyForm Noncommercial？
**A：** 因为目标要求同时满足「传染性（copyleft）」和「无授权禁止商用」。PolyForm Noncommercial 1.0.0 只禁止商用、没有 share-alike 条款；AGPL-3.0 提供传染性（含网络服务场景），附加商业使用限制条款后实现「商用需单独授权」。详见 `goal.md` QA-R004/QA-R005。

**Q：** 为什么不保留旧工具名（`get_compounds_by_cid` 等）作为别名？
**A：** 用户确认采用语义化命名且不要求向后兼容；保留别名会增加维护面并削弱命名规范的统一性。若未来需要兼容，可在 `registry.py` 低成本注册旧名转发。

**Q：** 光谱数据为什么不用 PubChemPy？
**A：** PubChemPy 未封装光谱接口（已核实其官方文档无 spectrum 支持）；光谱数据由 PubChem PUG-View 服务提供，需用 `requests` 直连。3D 结构则不同，PubChemPy 原生支持 `record_type='3d'`，无需直连。
