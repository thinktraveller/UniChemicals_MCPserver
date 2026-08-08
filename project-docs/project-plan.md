# pubchempy-mcp-server 构建计划书

> **版本状态**：v0.3.0 计划（步骤 1–7）已于 2026-08-08 完成并发布（提交 e44ecca / 39c0d74 验收通过）。自 2026-08-08 起，本文档新增 **v1.0.0 计划（步骤 8–13）**，其功能设计以 CAS Common Chemistry **官方 API 文档**为唯一权威依据（见步骤 8），参考项目仅作工具面与命名参考。

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

---

# v1.0.0 构建计划（基于 CAS Common Chemistry 官方文档）

## v1.0.0 项目概述

- **项目目标**：在 v0.3.0 完成的 PubChem MCP server 基础上接入 CAS/SciFinder 官方化学查询能力，形成 `pubchem` + `cas` 双数据库 MCP 服务；最终交付结构为 `src` 下仅有 `pubchem` 与 `cas` 两个包（`pubchem_mcp_server` 重命名为 `pubchem`）。完整目标与澄清见 `project-docs/goal.md` QA-R006。
- **功能设计依据（本次重设计要点）**：用户提供官方 API 文档 `reference-projects/CAS 常用化学 --- CAS Common Chemistry (2026_8_8 13：49：16).html`，明确测试 key（`CAS_COMMON_CHEMISTRY_API_KEY`）对应的是 **CAS Common Chemistry API**。官方文档定义该 key 可调用的全部能力为三个端点（Search / Detail / Export），本计划的功能范围、参数与响应结构**全部以该文档为准**。
- **参考项目定位（降级为参考）**：`reference-projects` 两个项目演示的是另外两套鉴权体系——CAS-Integration-API（`helium.cas.org`，OAuth2 client credentials）与 scifinder-api（`scifinder-n.cas.org`，OAuth2 授权码 + PKCE）。两者均**无法用本 key 调用**，故不作为功能来源，仅作为工具面设计（命名、参数风格、返回结构）与未来 Tier B 扩展的参考。

### v1.0.0 成功标准（与 goal.md QA-R006 一致）
- `src` 下仅有 `pubchem` 与 `cas` 两个包；`uv build` 通过；
- `cas_*` 工具覆盖官方文档三端点全部能力，且可被 MCP 客户端调用；
- 版本升至 1.0.0；README/README_zh 与工具清单一致；
- key 值不出现于任何文件、日志、提交与构建产物中。

## 官方文档端点规格（已核对，作为实现依据）

> 来源：`reference-projects/CAS 常用化学 --- CAS Common Chemistry (2026_8_8 13：49：16).html`（CAS Common Chemistry API 概览，OAS 2.0）。

- **Base URL**：`https://commonchemistry.cas.org/api`
- **鉴权**：请求头 `X-Api-Key`（值为注册后获得的 API token；Swagger 示例 cURL 写作 `X-API-KEY`，HTTP 头名大小写不敏感，但实现与探测统一采用文档正文的 `X-Api-Key`，以实测为准）。

| 端点 | 方法 | 参数 | 成功响应 | 错误码 |
|---|---|---|---|---|
| `/search` | GET | `q`（必填）：CAS RN（带/不带连字符）、SMILES（canonical/isomeric）、InChI（带/不带 `InChI=` 前缀）、InChIKey、名称（支持尾部通配符如 `car*`，不区分大小写）；`offset`、`size`（分页，每页最多 100；Swagger 中类型标注为 string，实际按数值传递，实测确认） | 200 `application/json`：`{"count": "<string>", "results": [{"rn", "name", "image"(SVG)}]}` | 400 / 500 |
| `/detail` | GET | `cas_rn` 或 `uri`（二选一） | 200 `application/json`：`uri`、`rn`、`name`、`image`(SVG)、`inchi`、`inchiKey`、`smile`、`canonicalSmile`、`molecularFormula`、`molecularMass`、`experimentalProperties[]`（name/property/sourceNumber）、`propertyCitations[]`（docUri/sourceNumber/source）、`synonyms[]`、`replacedRns[]` | 404 / 500 |
| `/export` | GET | `uri`（必填）、`returnAsAttachment`（boolean，默认 false） | 200 `text/plain`：molfile（V2000 文本，含物质名/分子式/RN/版权行） | 404 / 500 |

- 与旧计划的关键差异（旧 v1.0.0 计划已作废，本版为准）：`/search` 参数为 `q` + `offset` + `size`（**无** `match`/`length` 参数，名称模糊检索靠 `q` 尾部通配符实现）；`/export` 参数为 `uri` + `returnAsAttachment`；错误码为 400/404/500；`count` 为字符串。

## 工具映射表（端点 → 工具）

| 工具名 | 参数 | 底层端点 | 说明 |
|---|---|---|---|
| `cas_search_substance_by_name` | name, offset=0, size=10 | `GET /search?q={name}` | 支持尾部通配符（`car*`）、不区分大小写 |
| `cas_search_substance_by_casrn` | cas_rn, offset=0, size=10 | `GET /search?q={cas_rn}` | RN 带或不带连字符均可 |
| `cas_search_substance_by_smiles` | smiles, offset=0, size=10 | `GET /search?q={smiles}` | canonical / isomeric |
| `cas_search_substance_by_inchi` | inchi, offset=0, size=10 | `GET /search?q={inchi}` | 带或不带 `InChI=` 前缀 |
| `cas_search_substance_by_inchikey` | inchikey, offset=0, size=10 | `GET /search?q={inchikey}` | InChIKey 反查 |
| `cas_get_substance_by_casrn` | cas_rn | `GET /detail?cas_rn=` | 完整详情（含性质/同义词/replacedRns） |
| `cas_get_substance_by_uri` | uri | `GET /detail?uri=` | 完整详情（与上同构） |
| `cas_get_molfile_by_uri` | uri, return_as_attachment=False | `GET /export?uri=` | 返回 molfile 文本 |
| `cas_get_molfile_by_casrn` | cas_rn | 先 `GET /detail?cas_rn=` 取 uri，再 `GET /export?uri=` | 便捷两段封装 |
| `cas_get_properties_by_casrn` | cas_rn | `GET /detail?cas_rn=` 提取 | 便捷提取 experimentalProperties + propertyCitations（非独立端点） |
| `cas_get_image_by_casrn` | cas_rn | `GET /detail?cas_rn=` 提取 | 便捷提取 image SVG（非独立端点） |

> 说明：前 5 个搜索工具共享同一个 `/search` 端点，仅 `q` 语义不同；沿用 pubchem 的 `{数据库}_{动作}_{实体}_by_{标识符}` 命名规范拆分为可发现工具，底层共用 `client.search()`。便捷提取工具（properties/image）不增加 API 调用面，仅改善 AI 消费体验。

## 开发计划

### 步骤 8：官方文档核对、能力盘点与 API 只读探测

#### 目标说明
以官方文档为唯一权威规格固化三端点规格（上表）；用 `.env` 中的测试 key 做只读探测，验证鉴权头、参数、分页与错误码的真实行为，产出「端点规格 + 工具映射表」并写入 buildlog。

#### 具体操作
1. 通读官方 HTML 文档，将端点规格、参数、响应结构与错误码固化为文档表格（即本章节规格表），与官方文档逐条核对，无臆造端点/参数。
2. 只读探测（本地临时脚本，**不入库**）：
   ```python
   import os
   import requests
   from dotenv import load_dotenv

   load_dotenv()
   key = os.environ["CAS_COMMON_CHEMISTRY_API_KEY"]
   headers = {"X-Api-Key": key, "Accept": "application/json"}
   base = "https://commonchemistry.cas.org/api"
   # 1) 名称搜索（含通配符）
   requests.get(f"{base}/search", params={"q": "car*"}, headers=headers, timeout=30)
   # 2) RN / SMILES / InChI / InChIKey 搜索
   requests.get(f"{base}/search", params={"q": "50-00-0"}, headers=headers, timeout=30)
   requests.get(f"{base}/search", params={"q": "C=O"}, headers=headers, timeout=30)
   requests.get(f"{base}/search", params={"q": "InChI=1S/CH2O/c1-2/h1H2"}, headers=headers, timeout=30)
   requests.get(f"{base}/search", params={"q": "InChIKey=WSFSSNUMVMOOMR-UHFFFAOYSA-N"}, headers=headers, timeout=30)
   # 3) 分页：size=1 与 size=101（验证上限行为）、offset
   requests.get(f"{base}/search", params={"q": "car*", "offset": 0, "size": 1}, headers=headers, timeout=30)
   # 4) 详情：cas_rn 与 uri 两种取数
   requests.get(f"{base}/detail", params={"cas_rn": "50-00-0"}, headers=headers, timeout=30)
   requests.get(f"{base}/detail", params={"uri": "substance/pt/50000"}, headers=headers, timeout=30)
   # 5) molfile 导出
   requests.get(f"{base}/export", params={"uri": "substance/pt/50000"}, headers=headers, timeout=30)
   # 6) 错误路径：不存在 RN（预期 404/400）、空 q（预期 400）
   ```
3. 记录真实响应码、字段名、`count` 类型、分页上限、鉴权头大小写敏感性；将**脱敏**后的响应样例与结论写入 `project-docs/buildlog.md`。
4. 确认无 `match`/`length` 等臆造参数；若探测与文档有出入，以实测为准并在 buildlog 记录差异。
5. 安全：探测脚本仅本地运行，不提交；任何输出、日志、提交不得出现 key 值。

#### 验证方法
- 三端点全部探测成功；规格表与官方文档逐条对应，无臆造端点/参数；
- 明确回答「key 能打开哪个服务面」：仅 Common Chemistry 三端点；
- 401/403/429 等异常有记录与处理结论；
- key 值未出现在任何文件、日志、提交中。

#### 风险提示
- 调用 `commonchemistry.cas.org` 需要放行 HTTPS 网络（当前沙箱受限时需授权）；超时/限流（429）时采用退避重试，不当作代码错误；
- 若 key 已失效（401/403），暂停并通知用户轮换 key，不继续后续步骤；
- 鉴权头大小写、`size` 类型（Swagger 标注 string）等以实测为准。

### 步骤 9：`src/pubchem_mcp_server` → `src/pubchem` 重命名与影响面处理

#### 目标说明
交付结构要求 `src` 下仅有 `pubchem` 与 `cas` 两个包。本步骤把现包 `pubchem_mcp_server` 重命名为 `pubchem` 并处理全部引用面，保证 v0.3.0 的 40 个 `pubchem_*` 工具行为不变、构建与启动正常。

#### 具体操作
1. 目录重命名（保留历史）：
   ```powershell
   git mv src/pubchem_mcp_server src/pubchem
   ```
2. 全仓引用面核对（以 `rg -n "pubchem_mcp_server"` 为准，排除 `reference-projects` / `.venv` / `dist` / `.git` / `.codex`）：
   - `pyproject.toml`：`[project.scripts] pubchempy-mcp-server = "pubchem.server:main"`；`[tool.hatch.build.targets.wheel] packages = ["src/pubchem"]`；
   - `src/pubchem/` 内部确认均为相对导入（v0.3.0 重构后为 `from . import client` 形式，核对无绝对导入残留）；
   - `client.py` 的 `PUG_VIEW_USER_AGENT` 等字符串同步更新（如 `unichemicals-mcp-server/1.0`）；
   - README / README_zh / 文档与示例中的包名引用。
3. 清理构建缓存（`dist/`、`*.egg-info`、`__pycache__`）后 `uv build`，并 `uv run pubchempy-mcp-server` 启动冒烟（此时 cas 尚未接入，仅验证重命名无回归）。

#### 验证方法
- `uv build` 退出码 0，wheel 包含 `pubchem/server.py`；
- `uv run pubchempy-mcp-server` 正常启动、无 ImportError；
- `rg -n "pubchem_mcp_server"` 仅剩历史文档（buildlog/goal）中的合理引用。

#### 风险提示
- 旧构建缓存可能导致误判，先清理再构建；
- 若存在脚本/配置硬编码旧包名（如 MCP 客户端配置的入口路径），一并核对；
- 重命名只影响包目录与引用，不改变 `pubchem_*` 工具名（工具名以 `pubchem` 为数据库前缀，保持不变）。

### 步骤 10：`cas` 包骨架与鉴权客户端

#### 目标说明
建立 `src/cas/{__init__.py, client.py, utils.py}`。`client.py` 负责 `.env` 读取、API key 注入、HTTP 调用、超时/重试与错误归一化；`utils.py` 提供与 pubchem 一致的 `safe_execute` / `to_json_safe`；`registry.py` 在步骤 11 实现。

#### 具体操作
1. 依赖：`pyproject.toml` 显式声明 `python-dotenv>=1.0`（venv 中模块已存在，补声明即可）。
2. `src/cas/client.py` 骨架：
   ```python
   import os
   import requests
   from dotenv import load_dotenv

   BASE_URL = "https://commonchemistry.cas.org/api"   # 以步骤 8 实测为准
   API_KEY_ENV = "CAS_COMMON_CHEMISTRY_API_KEY"

   class CasApiError(RuntimeError):
       def __init__(self, status: int, message: str):
           super().__init__(f"CAS API HTTP {status}: {message}")
           self.status = status

   def _api_key() -> str:
       load_dotenv()
       key = os.environ.get(API_KEY_ENV)
       if not key:
           raise RuntimeError(f"环境变量 {API_KEY_ENV} 未配置（请在 .env 中设置）")
       return key

   def _headers() -> dict:
       return {"X-Api-Key": _api_key(), "Accept": "application/json"}  # 头名以步骤 8 实测为准

   def _get(path: str, params: dict) -> requests.Response:
       resp = requests.get(f"{BASE_URL}/{path}", params=params,
                           headers=_headers(), timeout=30)
       # 429/5xx 指数退避重试（最多 2 次）；最终失败抛 CasApiError
       return resp
   ```
3. 错误归一化：400 →「请求参数无效」；404 →「物质不存在或无效请求」；500 →「服务端错误」；429 →「限流，请稍后重试」；网络/超时异常也转为友好 `Error: ...` 形态（与 pubchem 一致）。
4. `/export` 返回 `text/plain`，客户端单独走 `resp.text`（不做 `.json()`）；`/search` 的 `count` 为字符串，序列化时原样保留。
5. `src/cas/utils.py`：`safe_execute` / `to_json_safe` 与 `pubchem.utils` 同构。两包各自持有（约 20 行），避免跨包导入耦合，保持 `src` 下仅两包的结构。
6. 安全：`_api_key()` 仅运行时读取；任何异常信息、日志、docstring 不得包含 key 值。

#### 验证方法
- 未配置 key 时工具返回明确的 `Error: 环境变量 CAS_COMMON_CHEMISTRY_API_KEY 未配置...`，不崩溃、不打印值；
- 最小冒烟：`uv run python -c "from cas.client import _headers"` 不输出 key；
- 429/503 重试与超时路径有处理逻辑（人工冒烟或最小单测）。

#### 风险提示
- key 过期/无效：步骤 8 探测即暴露，若 401/403 先暂停通知用户；
- 不要把 key 写入 `.env.example` 或任何提交文件（.env 已被 .gitignore 忽略）。

### 步骤 11：`cas` 工具实现与注册（覆盖官方文档全部能力）

#### 目标说明
按「工具映射表」实现 11 个 `cas_*` 工具：5 个搜索 + 2 个详情 + 2 个 molfile + 2 个便捷提取，全部基于官方文档三端点，命名沿用 `{数据库}_{动作}_{实体}_by_{标识符}`（数据库前缀 `cas`）。

#### 具体操作
1. `src/cas/registry.py` 配置驱动生成工具（与 pubchem 的 registry 同构），`register_all(mcp)` 统一注册：
   ```python
   # src/cas/registry.py
   from . import client
   from .utils import safe_execute

   def make_search_substance_by_name():
       def tool(name: str, offset: int = 0, size: int = 10) -> str:
           return safe_execute(client.search_substance, name, offset=offset, size=size)
       tool.__name__ = "cas_search_substance_by_name"
       tool.__doc__ = ("按名称搜索 CAS Common Chemistry 物质（支持尾部通配符如 car*，不区分大小写）。"
                       "返回 count 与 results(rn/name/image)。size 上限 100。")
       return tool
   ```
2. 参数校验：`size ∈ [1, 100]`（官方每页上限 100）、`offset ≥ 0`；非法参数返回明确 `Error: ...`。
3. 每个搜索工具 docstring 写明 `q` 语义：RN 可带/不带连字符；SMILES 支持 canonical/isomeric；InChI 可省略 `InChI=` 前缀；InChIKey 直接反查；名称支持尾部通配符。
4. `cas_get_molfile_by_casrn` 实现为两段调用：`/detail?cas_rn=` 取 `uri` → `/export?uri=` 取 molfile；`uri` 缺失时返回友好错误。
5. 便捷提取工具（`cas_get_properties_by_casrn`、`cas_get_image_by_casrn`）基于 `/detail` 响应字段提取，字段缺失时返回明确提示而非空串。
6. 失败形态与 pubchem 一致：成功返回 JSON 字符串（`to_json_safe`），失败返回 `Error: ...`。

#### 验证方法
- 真实调用 5 类搜索（`50-00-0`、`C=O`、`InChI=1S/CH2O/...`、`WSFSSNUMVMOOMR-UHFFFAOYSA-N`、`formaldehyde`/`car*`）均返回结果；
- `cas_get_substance_by_casrn("50-00-0")` 返回完整详情字段；`cas_get_substance_by_uri` 同构；
- `cas_get_molfile_by_casrn("50-00-0")` / `by_uri` 返回 molfile 文本（V2000）；
- `size=101` 与非法 offset 返回参数错误；不存在 RN 返回友好 404 错误；
- `tools/list` 出现全部 11 个 `cas_*` 工具，命名与映射表一致。

#### 风险提示
- 名称搜索可能返回多条结果，docstring 需说明分页参数（offset/size）并建议先 search 后 detail；
- `image` SVG 字符串较大（数 KB），返回前不截断，由客户端按需展示；
- 所有真实调用需网络可达 `commonchemistry.cas.org`；429 限流时工具返回明确限流提示而非崩溃。

### 步骤 12：双库统一注册、版本 1.0.0、依赖与文档

#### 目标说明
同一个 MCP server 同时暴露 `pubchem_*` 与 `cas_*` 工具；版本升至 1.0.0；README/README_zh 同步加入 CAS 接入说明、工具清单、数据来源与许可证声明。

#### 具体操作
1. `src/pubchem/server.py` 改为双库注册：
   ```python
   from mcp.server.fastmcp import FastMCP
   from pubchem.registry import register_all as register_pubchem
   from cas.registry import register_all as register_cas

   mcp = FastMCP("UniChemicals_MCP_Server")   # 服务名变更属预期破坏性变更
   register_pubchem(mcp)
   register_cas(mcp)
   ```
2. `pyproject.toml`：`version = "1.0.0"`；dependencies 增加 `python-dotenv>=1.0`；description 更新为「多数据库（PubChem + CAS Common Chemistry）化学查询 MCP 服务」。
3. 新增 `.env.example`（仅含键名占位，**无真实值**）：
   ```env
   CAS_COMMON_CHEMISTRY_API_KEY=your_api_key_here
   ```
4. `README.md` / `README_zh.md`：
   - 新增「CAS / SciFinder 化学查询」章节：环境变量 `CAS_COMMON_CHEMISTRY_API_KEY`、`.env.example` 配置示例、11 个 `cas_*` 工具清单、数据来源（CAS Common Chemistry）、频率与限流提示；
   - 许可证与归属章节：参考项目（CAS-Integration-API / scifinder-api，Apache-2.0）仅作接口参考，不得整体复制代码并保留署名；CAS Common Chemistry 数据的使用条款以官方页面为准，README 声明数据归属（预期含非商业限制，步骤 8 一并核实官方页面条款）；
   - 工具总数（40 个 `pubchem_*` + 11 个 `cas_*`）与示例命令更新。

#### 验证方法
- `uv build` 通过，wheel 同时包含 `pubchem` 与 `cas` 两个包；
- MCP 握手 `tools/list` 同时出现 40 个 `pubchem_*` 与 11 个 `cas_*` 工具，数量与命名和文档一致；
- 版本号在 `pyproject.toml`、README、wheel 元数据中均为 1.0.0；
- 全文检索不到真实 key 值；`.env.example` 只含占位符。

#### 风险提示
- README 中英文不同步是常见问题，两文件必须同时修改；
- FastMCP 服务名变更会改变 `serverInfo`，属预期破坏性变更，README 说明即可；
- PyPI 包名保持 `pubchempy-mcp-server`（避免改名带来的下游断裂），描述中说明 v1.0.0 已是多数据库服务。

### 步骤 13：端到端验收与安全审计

#### 目标说明
对照 goal.md QA-R006 的成功标准做最终验收：结构、构建、工具可用性、文档、key 安全五方面逐项确认。

#### 具体操作
1. 结构验收：`Get-ChildItem src` 只有 `pubchem` 与 `cas`；`rg -n "pubchem_mcp_server"` 仅剩历史文档引用。
2. 构建与启动：`uv build`；`uv run pubchempy-mcp-server`。
3. MCP 冒烟：initialize → `tools/list` → 至少各一条 pubchem 与 cas 真实查询（如 `pubchem_search_compound_by_cid(2244)`、`cas_get_substance_by_casrn("50-00-0")`、`cas_get_molfile_by_casrn("50-00-0")`、InChIKey 搜索）。
4. 安全审计：
   ```powershell
   git grep -n "CAS_COMMON_CHEMISTRY_API_KEY" -- ':!.env'   # 只允许键名占位，无值
   git status --short                                        # 无 .env、无 key 相关文件入库
   ```
   检查 `dist/` 产物与日志无 key 明文。
5. 文档一致性：README/README_zh 工具清单与 `tools/list` 一致。
6. `project-docs/buildlog.md` 记录每一步结果（步骤 8–13）并提交。

#### 验证方法
- 上述 5 项全部通过即 v1.0.0 完成。

#### 风险提示
- key 可能因限流在验收时临时返回 429，需区分「代码错误」与「限流」，重试或等待后复验；
- 若步骤 8 发现 key 失效，v1.0.0 验收前必须先轮换 key；
- 参考项目能力（结构搜索/文档/Markush/商业来源/光谱）不属于本 key 可用面，README 需明确边界，避免过度承诺。

## v1.0.0 Q&A 记录（官方文档版）

**Q：** 为什么本次以官方文档为设计依据，参考项目降级为参考？
**A：** 测试 key 名为 `CAS_COMMON_CHEMISTRY_API_KEY`，明确指向 CAS Common Chemistry API；用户提供的官方 HTML 文档（OAS 2.0）定义了该 key 可调用的全部三个端点。参考项目演示的 Integration API（client credentials）与 SciFinder-n（OAuth2 + PKCE）需要另外的凭据体系，本 key 无法调用，因此不作为功能来源，仅作工具命名与返回结构参考。

**Q：** 官方文档下 key 能实现的「全部功能」具体指什么？
**A：** 三端点全量：`/search` 的 5 类检索（CAS RN / SMILES / InChI / InChIKey / 名称+尾部通配符，含 offset/size 分页）、`/detail` 的完整物质详情（结构标识符、分子式/质量、实验性质与引用、同义词、被替代 RN、SVG 结构图）、`/export` 的 molfile 导出；外加 2 个基于 detail 的便捷提取工具（性质、结构图）。结构搜索/文档/反应/Markush/商业来源/光谱属于 Integration API 或 SciFinder-n 能力，本 key 不支持。

**Q：** `/search` 为什么拆成 5 个工具？
**A：** 同一端点、不同 `q` 语义；沿用 pubchem 的 `{数据库}_{动作}_{实体}_by_{标识符}` 命名规范，便于 AI 按标识符类型发现与调用；底层共用 `client.search()`，无重复实现。

**Q：** 为什么 `cas` 与 `pubchem` 各自持有 utils 中的 `safe_execute` / `to_json_safe`？
**A：** 交付结构要求 `src` 下仅有 `pubchem` 与 `cas` 两包，不引入公共包；这两个辅助函数体量很小（约 20 行），各自持有以避免跨包耦合，代价是少量重复，可接受。

**Q：** 官方文档与旧 v1.0.0 计划的关键差异是什么？
**A：** `/search` 参数为 `q` + `offset` + `size`（旧计划臆测了 `match`/`length`）；`/export` 参数为 `uri` + `returnAsAttachment`；鉴权头官方正文为 `X-Api-Key`（curl 示例为 `X-API-KEY`，实测确认大小写敏感性）；错误码为 400/404/500；`count` 为字符串；`/detail` 的 404 描述为 Invalid Request（无效请求）。

# v1.1.0 构建计划（包名统一：pubchempy-mcp-server → unichemicals-mcp-server）

> **版本状态**：本增量章节规划把发行包名从 `pubchempy-mcp-server` 统一为 `unichemicals-mcp-server`（PyPI 规范名，与用户提出的 `unichemicals_mcpserver` 等价），背景是 v1.0.0 后服务已同时接入 PubChem 与 CAS 两个数据源，旧名不再贴切。此节**推翻**步骤 12/13 中「PyPI 包名保持 pubchempy-mcp-server 避免下游断裂」的旧决策（理由见文末 Q&A）。已有步骤 1–13 与既有 Q&A 内容保持不变，本次仅增量追加。

> **执行状态（2026-08-08 23:55）**：用户已确认三项待确认项（包名 `unichemicals-mcp-server`；PyPI 发布由用户自行执行；统一 FastMCP 显示名 / User-Agent）。步骤 14–18 已执行完成并通过验证，详见 `project-docs/buildlog.md`；步骤 19（PyPI 发布）留给用户执行。

## 影响面清单（主 agent 已核查，执行时逐一核对）

| 文件 | 位置 | 改动 |
|---|---|---|
| `pyproject.toml` | `[project] name` | `pubchempy-mcp-server` → `unichemicals-mcp-server` |
| `pyproject.toml` | `[project.scripts]` | `pubchempy-mcp-server = "pubchem.server:main"` → 新命令名 = `"pubchem.server:main"` |
| `uv.lock` | 根包 `name` | 由 `uv lock` 重新生成（勿手改） |
| `mcp-client-example.json` | `args` | `uvx --refresh` 旧名 → 新名 |
| `README.md` / `README_zh.md` | PyPI 徽章、客户端配置示例、`uv run` 命令 | 旧名 → 新名 |
| `src/pubchem/server.py` | FastMCP 显示名 | 已统一为 `unichemicals-mcp-server`（用户确认） |
| `src/pubchem/client.py` | User-Agent | 已是 `unichemicals-mcp-server/1.0`，默认不改 |
| `pyproject.toml` 依赖 | `pubchempy>=1.0.5` | 第三方库 PubChemPy，**禁止修改** |
| `project-docs/*` | 历史引用 | 历史记录，默认不回改 |

## 开发计划

### 步骤 14：确认最终包名与 PyPI 可用性

#### 目标说明
先锁定最终写法并确认 PyPI 上该规范名可用，避免后续返工；发布前检查是改名流程的第一道闸门。

#### 具体操作
1. 确定规范名：推荐 `unichemicals-mcp-server`（PyPI 将 `_`/`-`/大小写归一化，与 `unichemicals_mcpserver` 是同一个规范名；连字符风格与旧名 `pubchempy-mcp-server` 一致）。
2. 检查 PyPI 占用情况（PowerShell）：
   ```powershell
   try {
       $r = Invoke-RestMethod -Uri 'https://pypi.org/pypi/unichemicals-mcp-server/json' -TimeoutSec 30
       "已占用: $($r.info.name) $($r.info.version)"
   } catch {
       "未占用（404）: $($_.Exception.Message)"
   }
   ```
3. 与用户确认最终写法（连字符或下划线）后进入步骤 15。

#### 验证方法
- PyPI 返回 404（未被他人占用），或确认占用者为用户本人旧包；
- 用户确认最终名字写法。

#### 风险提示
- 因 PyPI 归一化，`unichemicals_mcpserver` 与 `unichemicals-mcp-server` 只需查一次占用；
- 若规范名已被他人占用，需更换候选名（如加后缀），不得与既有包混淆。

### 步骤 15：修改 pyproject.toml（name + [project.scripts]）

#### 目标说明
把发行名与控制台命令改为新名；入口仍指向 `pubchem.server:main`，源码与工具行为零改动。

#### 具体操作
1. 编辑 `pyproject.toml`：
   ```toml
   [project]
   name = "unichemicals-mcp-server"
   # version / description / dependencies 保持不变

   [project.scripts]
   unichemicals-mcp-server = "pubchem.server:main"
   ```
2. 保留 `pubchempy>=1.0.5` 依赖（第三方库 PubChemPy，勿改）。

#### 验证方法
- `Select-String pyproject.toml -Pattern 'name = "unichemicals'` 命中；
- `rg -n "pubchempy-mcp-server" pyproject.toml` 无结果（依赖 `pubchempy>=1.0.5` 除外）。

#### 风险提示
- 只改 `name` 与 `[project.scripts]` 两处，误改依赖名会导致安装失败；
- 用户已确认统一 FastMCP 显示名，本步骤同步将 `src/pubchem/server.py` 的 `FastMCP(...)` 显示名改为 `unichemicals-mcp-server`。

### 步骤 16：重新生成 uv.lock

#### 目标说明
`uv.lock` 中的根包名由 pyproject 生成，需重新锁定，避免锁文件与包元数据不一致。

#### 具体操作
```powershell
uv lock
```

#### 验证方法
- `Select-String uv.lock -Pattern 'name = "unichemicals-mcp-server"'` 命中根包；
- `rg -n 'name = "pubchempy-mcp-server"' uv.lock` 无结果（`name = "pubchempy"` 依赖项保留属正常）。

#### 风险提示
- uv 版本过旧导致 lock 失败时，先 `uv self update`，或用 `uv sync` 触发重锁；
- lock 变更应只涉及根包名相关行；若出现大范围 diff，需检查 pyproject 是否有意外改动。

### 步骤 17：更新客户端示例与中英文 README

#### 目标说明
让用户按新名字接入，避免 README、示例与发布包不一致。

#### 具体操作
1. `mcp-client-example.json`：`"args": ["--refresh", "unichemicals-mcp-server"]`。
2. `README.md` / `README_zh.md` 三处同步修改：
   - PyPI 徽章 URL（`badge.fury.io/py/…` 与链接地址）→ 新名；
   - MCP 客户端配置示例 `uvx --refresh <新名>`；
   - 本地启动命令 `uv run <新名>`。
3. 保留 PubChemPy 致谢段落与「依赖第三方库 PubChemPy」说明。

#### 验证方法
- `ConvertFrom-Json mcp-client-example.json` 解析成功；
- `rg -n "pubchempy-mcp-server" README.md README_zh.md mcp-client-example.json` 无结果。

#### 风险提示
- 中英文文档不同步是高频问题，两个文件必须同时修改；
- 徽章在包发布前显示 unknown 属预期，发布后自动恢复。

### 步骤 18：构建、本地冒烟与残留检查

#### 目标说明
验证改名后构建产物、入口命令与 MCP 服务全部正常，并确认全仓无旧名残留（历史文档除外）。

#### 具体操作
```powershell
uv build
uv run unichemicals-mcp-server   # 冒烟：initialize → tools/list → 51 工具
rg -n -i "pubchempy-mcp-server" -S --glob '!.git/**' --glob '!reference-projects/**' --glob '!dist/**' --glob '!.venv/**' .
```

#### 验证方法
- `uv build` 成功，dist 产物名为 `unichemicals_mcp_server-*.whl`；
- wheel 内 `entry_points.txt` 为 `unichemicals-mcp-server = pubchem.server:main`；
- MCP 握手 `serverInfo` = `unichemicals-mcp-server`，`tools/list` 51 个工具（40 pubchem + 11 cas）无回归；
- `rg` 残留仅剩 `project-docs/` 历史文档引用（预期保留，不回改）。

#### 风险提示
- 旧虚拟环境中入口命令可能不生效，删除重建 `.venv` 或确认 `uv run` 使用最新 pyproject；
- 清理 `dist/` 旧产物避免混淆（`Remove-Item dist -Recurse -Force`；该目录已被 gitignore，不影响仓库）。

### 步骤 19：PyPI 发布与下游接入验证（需用户授权）

#### 目标说明
把新名发布到 PyPI，并验证 `uvx` 远程接入；旧包保留以兼容已接入的客户端。

#### 具体操作
```powershell
uv publish
uvx --refresh unichemicals-mcp-server
```

#### 验证方法
- PyPI 页面 `https://pypi.org/project/unichemicals-mcp-server/` 可访问且版本正确；
- `uvx` 独立环境 MCP 握手正常，`tools/list` 51 个工具；
- 旧包 `pubchempy-mcp-server` 0.3.0 保持不动（README 可选加一行迁移说明）。

#### 风险提示
- PyPI 不允许覆盖已发布版本，发布前确认版本号：1.0.0 尚未以任何名字发布过则直接首次发布 1.0.0；若已发布过旧名 1.0.0 则升级为 1.1.0；
- `uv publish` 需要 PyPI 凭据与用户授权，未授权不得执行；
- 已配置旧包名的客户端需更新配置后才可接入新包。

## v1.1.0 Q&A 记录（改名版）

**Q：** 用户写的 `unichemicals_mcpserver` 和 `unichemicals-mcp-server` 是同一个名字吗？
**A：** PyPI 对包名做归一化（`_`/`-`/大小写视为同一规范名），两者在 PyPI 上是同一个包；推荐连字符写法，与现有 `pubchempy-mcp-server` 风格一致。控制台命令名则以 `pyproject.toml` 的 `[project.scripts]` 中写的为准。

**Q：** 为什么推翻步骤 12/13「PyPI 包名保持不变」的旧决策？
**A：** 该决策的背景是 v1.0.0 接入 CAS 后仍沿用旧名以避免下游断裂；但服务已成为双数据源，旧名 `pubchempy` 无法表达 UniChemicals 定位，且 1.0.0 尚未发布、改名无存量用户成本，属于零成本改名窗口。

**Q：** 服务显示名 `UniChemicals_MCP_Server` 和 User-Agent 要不要一起改？
**A：** 用户已确认统一：FastMCP 显示名已从 `UniChemicals_MCP_Server` 改为 `unichemicals-mcp-server`（与包名一致，`serverInfo` 相应变化属预期破坏性变更）；User-Agent 此前已是 `unichemicals-mcp-server/1.0`，保持不动。

**Q：** `project-docs/` 下的历史引用要回改吗？
**A：** 默认不回改：goal / project-plan / buildlog / teach 是历史记录，记录当时的事实与决策；只需更新面向未来的文档（README、示例、本次新步骤）。

**Q：** 改名对已发布 0.3.0 的用户有影响吗？
**A：** 旧包 `pubchempy-mcp-server` 0.3.0 保留在 PyPI，原有客户端配置继续可用；新用户按新名接入。如需提示迁移，在 README 加一行说明即可。

## 待用户确认项

1. ✅（2026-08-08 已确认）最终包名：`unichemicals-mcp-server`；
2. ✅（2026-08-08 已确认）PyPI 发布由用户自行执行，步骤 19 不纳入本次构建；
3. ✅（2026-08-08 已确认）统一 FastMCP 显示名 / User-Agent（显示名改为 `unichemicals-mcp-server`，User-Agent 保持 `unichemicals-mcp-server/1.0`）。
