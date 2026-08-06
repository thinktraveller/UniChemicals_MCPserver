# 构建日志

## [2026-08-06 23:15] 步骤 1 完成：修正打包配置并跑通 `uv build`

### 执行的任务
- 将源码目录 `src/pubchempy_mcpserver` 统一重命名为 `src/pubchem_mcp_server`，与 `pyproject.toml` 中的包路径声明对齐（`git mv`，保留历史记录）。
- 在 `pyproject.toml` 中补充许可证元数据：`license = "AGPL-3.0-only"`、`license-files = ["LICENSE"]`。
- 执行 `uv build`，成功生成 wheel 与 sdist 两种构建产物。

### 关键变更
- `src/pubchempy_mcpserver/` → `src/pubchem_mcp_server/`（目录重命名，含 `__init__.py`、`server.py`）
- `pyproject.toml`：新增 `license` 与 `license-files` 字段
- 新增 `dist/pubchempy_mcp_server-0.1.1-py3-none-any.whl`、`dist/pubchempy_mcp_server-0.1.1.tar.gz`（被 `.gitignore` 忽略，不入库）

### 验证结果
- `uv build` 退出码 0，成功构建 wheel + sdist；
- 解包检查 wheel：包含 `pubchem_mcp_server/__init__.py` 与 `pubchem_mcp_server/server.py`；
- `entry_points.txt` 正确：`pubchempy-mcp-server = pubchem_mcp_server.server:main`；
- `METADATA` 正确：`License-Expression: AGPL-3.0-only`、`License-File: LICENSE`、`Requires-Python: >=3.10`。
- ⏳ 待办：入口点启动冒烟测试（`uv run pubchempy-mcp-server`）依赖虚拟环境，等用户完成环境搭建后补跑。

### 遇到的问题及解决方案
- 计划书环境命令 `uv pip install -e ".[dev]"` 中的 `[dev]` 附加依赖组在当前 `pyproject.toml` 中不存在，直接执行会报错。已改为 `uv pip install -e .`，如需开发依赖组（如 pytest）可在后续步骤补充。

### 下一步计划
- 步骤 2：模块化重构（拆分为 server.py / registry.py / client.py / utils.py，引入工具工厂消除重复）。

---

## [2026-08-07 01:05] 步骤 2 完成：模块化重构（工具工厂消除重复）

### 执行的任务
- 将单文件 `server.py`（40+ 复制粘贴工具）拆分为四个模块：
  - `server.py`：FastMCP 实例、`register_all(mcp)` 注册入口、`main()`
  - `registry.py`：声明式工具注册表 + 工厂函数，按命名空间列表批量生成工具
  - `client.py`：PubChemPy 调用封装层（工具不再直接依赖 pubchempy）
  - `utils.py`：`_safe_execute` 迁移（`safe_execute` / `to_json_safe` 序列化与异常捕获）
- 工具工厂覆盖全部工具族：化合物搜索、属性、同义词、物质搜索（含 sourceid 特判）、测定、CID/SID/AID 解析、下载。

### 关键变更
- 新增 `src/pubchem_mcp_server/utils.py`、`client.py`、`registry.py`
- 重写 `src/pubchem_mcp_server/server.py`（13KB → 精简入口）

### 验证结果
- MCP 握手 + `tools/list`：工具数量 41，名称与注册顺序和重构前完全一致（`ORDER_MATCH: True`）；
- 抽查参数 schema 一致：`get_compounds_by_cid`（identifier: integer）、`get_properties_by_cid`（properties: array[string]）、`get_substances_by_sourceid`（sourceid + source_name）、`download_by_cid`（overwrite 可选 bool）；
- 真实调用冒烟（PubChem REST，网络）：
  - `get_compounds_by_cid(2244)` 返回阿司匹林完整记录；
  - `get_cids_by_name("aspirin")` 返回 `[2244]`；
  - `get_properties_by_cid(["MolecularFormula","MolecularWeight"], 2244)` 返回 C9H8O4 / 180.16；
  - `get_synonyms_by_cid(2244)` 返回同义词列表（aspirin、ACETYLSALICYLIC ACID 等）。

### 遇到的问题及解决方案
- 用户执行 `uv venv` 重建了 `.venv`（清空已装包），且 `uv pip install -e .` 因未激活虚拟环境装到了 Anaconda base（`c:\ProgramData\anaconda3`）。已用 `uv sync` 重新填充 `.venv`；后续统一用 `uv run`/`uv sync` 管理环境，不再手动激活。
- pubchempy 1.0.5 内部使用 `urllib`（无 requests 超时参数，`**kwargs` 会变成 URL 查询参数），已在 `client.py` 用 `socket.setdefaulttimeout(30)` 兜底防挂起。
- 测试脚本一次性写入多条 JSON-RPC 后立即关闭 stdin，最后一条网络请求的响应会被 EOF 中断，属测试伪信号；改为延迟关闭 stdin 后验证通过。

### 下一步计划
- 步骤 3：工具语义化命名（`pubchem_{动作}_{实体}_by_{标识符}`），删除旧名不留别名。

---

## [2026-08-07 01:15] 步骤 3 完成：工具语义化命名

### 执行的任务
- 按 `{数据库}_{动作}_{实体}_by_{标识符}` 规范重写 `registry.py` 中全部工具的注册名与函数名，动作词表固定为 `search`（查记录）/ `get`（取属性/同义词）/ `resolve`（标识符转换）。
- 新旧命名映射：
  - `get_compounds_by_*` → `pubchem_search_compound_by_*`（7 个）
  - `get_substances_by_sid/name/sourceid` → `pubchem_search_substance_by_*`（3 个）
  - `get_assays_by_aid` → `pubchem_search_assay_by_aid`（1 个）
  - `get_properties_by_*` → `pubchem_get_property_by_*`（7 个）
  - `get_synonyms_by_*` → `pubchem_get_synonym_by_*`（7 个）
  - `get_cids_by_*` → `pubchem_resolve_cid_by_*`（5 个）
  - `get_sids_by_*` → `pubchem_resolve_sid_by_*`（2 个）
  - `get_aids_by_*` → `pubchem_resolve_aid_by_*`（2 个）
- 全部工具 docstring 重写，注明参数含义与返回值；不保留旧名别名。

### 关键变更
- `src/pubchem_mcp_server/registry.py`：工具名与 docstring 全面更新（工厂与注册表结构不变）

### 验证结果
- `tools/list`：总计 41 个工具；34 个 `pubchem_*` 前缀语义化名称 + 7 个 `download_by_*`（步骤 4 将移除）；旧名（`get_compounds_by_*` 等）零残留；
- 工具描述正常展示（含参数说明与返回说明）；
- 真实调用冒烟（PubChem REST，网络）：
  - `pubchem_search_compound_by_cid(2244)` 返回阿司匹林记录；
  - `pubchem_resolve_cid_by_name("aspirin")` 返回 `[2244]`；
  - `pubchem_get_synonym_by_cid(2244)` 返回同义词列表。

### 遇到的问题及解决方案
- 计划书步骤 3 的验证标准写的是「工具列表全部符合 pubchem_* 前缀规范」，但下载工具不在动作词表（search/get/resolve）内且步骤 4 将整体移除。为避免无谓的临时改名，7 个 `download_by_*` 保持原名，在步骤 4 直接删除；已与计划书映射表（未包含 download 行）保持一致。
- 测试脚本并发发送多条 tools/call 后关闭 stdin，最后一条网络响应被 EOF 截断（测试伪信号）；改为逐条发送并等待响应后验证通过。

### 下一步计划
- 步骤 4：移除 6 个 `download_by_*` 下载工具（实际为 7 个：cid/name/smiles/sdf/inchi/inchikey/formula），同步 README/README_zh、许可证元数据说明，版本号升至 0.2.0。

---

## [2026-08-07 01:24] 步骤 4 完成：移除下载工具并同步文档与许可证元数据

### 执行的任务
- 从 `registry.py` 删除 `_make_download` 工厂与 7 个 `download_by_*` 工具注册（cid/name/smiles/sdf/inchi/inchikey/formula，计划书写 6 个为笔误，实际 7 个）；
- 从 `client.py` 删除 `download()` 封装（不再调用 `pcp.download`）；
- 重写 `README.md` 与 `README_zh.md`：
  - 工具清单全部替换为 34 个语义化新名称（search/get/resolve 六组）；
  - 删除「文件下载」工具组及所有下载示例/介绍；
  - 新增「数据来源」说明：所有数据实时来自 PubChem 官方 REST 服务（PUG REST / PUG-View），无本地缓存；
  - 许可证章节补充说明：AGPL-3.0 具传染性 + 商用需单独授权。
- 版本号 `0.1.1 → 0.2.0`（破坏性变更）。

### 关键变更
- `src/pubchem_mcp_server/registry.py`：删除下载工厂与注册
- `src/pubchem_mcp_server/client.py`：删除 `download()`
- `README.md` / `README_zh.md`：工具清单、数据来源、许可证说明全面更新
- `pyproject.toml`：`version = "0.2.0"`

### 验证结果
- `tools/list`：总计 34 个工具，全部为 `pubchem_*` 前缀，无任何 download 工具；
- README/README_zh 全文检索：无 `download_by_`、无「文件下载」、无旧工具名（`get_compounds_by_*` 等）残留；
- `uv build` 成功生成 `pubchempy_mcp_server-0.2.0` wheel + sdist；
- 0.2.0 wheel METADATA 验证：`Version: 0.2.0`、`License-Expression: AGPL-3.0-only`、`License-File: LICENSE`；
- 清理 dist 中过期的 0.1.1 旧构建产物（避免步骤 7 误传）。

### 遇到的问题及解决方案
- 无（计划书「6 个下载工具」与实际 7 个的差异已在步骤 3 记录并按实际数量处理）。

### 下一步计划
- 步骤 5：补充工具族（批量查询、3D conformer、描述符、原子/键结构），继续挖掘 PubChemPy 能力。

---

## [2026-08-07 01:35] 步骤 5 完成：补充工具族（批量/3D/描述符/原子键）

### 执行的任务
- 先联网实测 PubChemPy 1.0.5 能力，确认真实返回结构后实现 5 个新工具：
  - `pubchem_search_compound_by_cids`：CID 列表批量查询（实测 [2244,2245,2246] 返回 3 条记录）
  - `pubchem_get_property_by_cids`：CID 列表批量属性
  - `pubchem_get_conformer_by_cid`：3D 构象（`record_type='3d'`，返回原子 x/y/z 坐标与键）
  - `pubchem_get_descriptor_by_cid`：计算描述符全集（默认 21 项：MolecularFormula/MolecularWeight/ExactMass/XLogP/TPSA/Complexity/Charge/HBD/HBA/RotatableBond/HeavyAtom/IsotopeAtom/立体计数/Volume3D 等；支持可选 properties 列表）
  - `pubchem_get_structure_by_cid`：原子/键拓扑（`vars(atom)` / `vars(bond)` 提取 aid/element/坐标/键级）
- 新增 `client.get_conformer()` 与 `client.get_structure()`；`utils.to_json_safe` 增加 to_dict 失败的兜底序列化。
- README.md / README_zh.md 同步：工具数 34 → 39，新增批量与 3D/描述符章节。

### 关键变更
- `src/pubchem_mcp_server/client.py`：新增 `get_conformer()`、`get_structure()`
- `src/pubchem_mcp_server/registry.py`：新增 `DEFAULT_DESCRIPTORS` 常量与 5 个工具工厂/注册
- `src/pubchem_mcp_server/utils.py`：`to_json_safe` 兜底 + `_json_default` 递归序列化
- `README.md` / `README_zh.md`：工具清单更新

### 验证结果
- `tools/list`：39 个工具，5 个新工具 schema 正确（cids: array[integer]、properties 可选数组等）；
- 真实调用（联网）全部通过：
  - 批量查询返回 3 条记录；批量属性返回 2244/2245 的属性字典；
  - `pubchem_get_conformer_by_cid(2244)` 返回 `coordinate_type: "3d"` + 带 z 坐标的原子；
  - `pubchem_get_descriptor_by_cid(2244)` 返回 21 项描述符；
  - `pubchem_get_structure_by_cid(2244)` 返回 atoms/bonds 拓扑；
  - 错误路径：非法 CID 返回友好 `Error: PubChem HTTP Error 400 ...`，服务不崩溃。

### 遇到的问题及解决方案
- **PubChemPy 1.0.5 已知缺陷**：`Compound.to_dict()` 会触发 `cactvs_fingerprint` 属性（`self.fingerprint[8:]`），3D 记录缺 fingerprint 字段导致 `'NoneType' object is not subscriptable`。已按根因修复：conformer 工具改用 `client.get_conformer` 手工构建字典（不经过 to_dict），并在 `utils.to_json_safe` 增加兜底递归序列化，防御其他记录类型。
- 描述符属性名初测含无效项 `ConformerModel3D`（PUG REST 返回 400 Invalid property），逐名实测后从默认集剔除；默认集 21 项均为已验证合法属性名。
- 批量请求限制：docstring 已注明单次不超过 100 个 CID。

### 下一步计划
- 步骤 6：新增 PUG-View 直连能力（光谱工具），`pyproject.toml` 增加 `requests` 依赖。

---

## [2026-08-07 02:00] 步骤 6 完成：PUG-View 直连光谱工具

### 执行的任务
- `pyproject.toml` 新增依赖 `requests>=2.31`（实际解析 2.34.2），`uv sync` 安装成功；
- 实测 PUG-View「Spectral Information」真实 JSON 结构（CID 2244）：`Record.Section` 树包含 1D/2D NMR、Mass Spectrometry（GC-MS/MS-MS/LC-MS）、UV、IR（FTIR/ATR-IR）、Raman 等；`Information` 节点值形态：`StringWithMarkup`（734 个）、`ExternalDataURL+MimeType` 图片链接（79 个）、`Number`（32 个）；
- `client.py` 新增 PUG-View 直连封装：
  - `fetch_pug_view()`：30s 超时、503/网络错误退避重试 3 次、自定义 User-Agent；
  - `get_spectrum()` / `parse_spectrum_section()`：按 TOCHeading 定位光谱类型（支持别名如 1H NMR/FTIR/GC-MS 与大小写不敏感的完整标题），按 ReferenceNumber 分组解析光谱，无该类型数据时抛出明确 ValueError；
  - `SPECTRUM_TYPE_ALIASES`：用户友好类型 → PUG-View 标题映射。
- `registry.py` 新增工具 `pubchem_get_spectrum_by_cid(cid, spectrum_type)`（经 `safe_execute` 统一异常处理）。
- README/README_zh 同步：工具数 39 → 40，新增光谱工具说明。

### 关键变更
- `pyproject.toml`：新增 `requests>=2.31`
- `src/pubchem_mcp_server/client.py`：PUG-View 封装 + 光谱解析（约 120 行）
- `src/pubchem_mcp_server/registry.py`：光谱工具工厂与注册
- `README.md` / `README_zh.md`：工具清单更新

### 验证结果
- `tools/list`：40 个工具，`pubchem_get_spectrum_by_cid` 存在，schema 为 cid(int) + spectrum_type(str)；
- 真实调用（联网）全部通过：
  - `1H NMR`：返回 Spectra ID 1776、Instrument Type Bruker、600 MHz 等完整字段；
  - `13C NMR`：Spectra ID 3097、峰值表 `Shifts [ppm]:Intensity`；
  - `GC-MS`：Spectra ID 1003、Top 5 Peaks 等；
  - `IR`：父级标题查询自动包含子类数据（FTIR/ATR-IR）；
  - 错误路径：非法 CID 返回友好 `Error: 400 Client Error: PUGVIEW.BadRequest ...`，服务不崩溃；
- `uv build` 成功（0.2.0）。

### 遇到的问题及解决方案
- 初测时 `requests` 未安装（ModuleNotFoundError）——本就是本步骤新增依赖，加入 `pyproject.toml` 后 `uv sync` 解决；
- PUG-View 返回结构复杂（Section/Information 多层嵌套、值形态多样），按真实响应核对后实现三种值形态提取（StringWithMarkup 多段用 `; ` 连接、Number+Unit、ExternalDataURL 图片链接），并对无数据光谱返回明确错误。

### 下一步计划
- 步骤 7：端到端验证（`uv build` + `uvx --refresh` 远程 MCP 服务跑通）与 PyPI 发布。

---

## [2026-08-06 23:35] 步骤 1 补充修复：mcp 2.0 移除 FastMCP，锁定 1.x 并完成入口冒烟测试

### 执行的任务
- 用户执行 `uv run pubchempy-mcp-server` 冒烟测试时发现 `ModuleNotFoundError: No module named 'mcp.server.fastmcp'`。
- 诊断根因：依赖约束 `mcp[cli]>=1.0.0` 解析到了最新的 mcp 2.0.0，而 mcp 2.0 已从 SDK 中移除 `FastMCP`（高层 API 迁出），`mcp/server/` 下不再有 `fastmcp.py`（本地已核实）。
- 修复：按构建计划书技术选型（FastMCP + mcp 1.x API），将依赖收紧为 `mcp[cli]>=1.0.0,<2.0`，执行 `uv sync` 将环境降级到 mcp 1.29.0。

### 关键变更
- `pyproject.toml`：`mcp[cli]>=1.0.0` → `mcp[cli]>=1.0.0,<2.0`
- 环境：`.venv` 中 mcp 2.0.0 降级为 1.29.0（`uv.lock` 按 `.gitignore` 规则不入库）

### 验证结果
- `uv sync` 成功，mcp 1.29.0 安装完成；
- `uv run python -c "from pubchem_mcp_server.server import mcp"` 导入通过；
- 真实 MCP 握手冒烟测试通过：发送 `initialize` → `initialized` → `tools/list`，服务正常响应，`serverInfo` = PubChemPy_MCP_Server / 1.29.0，`tools/list` 返回 41 个工具，进程退出码 0。

### 遇到的问题及解决方案
- mcp 2.0.0 移除 `mcp.server.fastmcp`，是上游破坏性变更，计划书风险提示未覆盖；已按计划书技术选型锁定 1.x 处理。
- 测试过程中 PowerShell 管道向 stdio 服务喂入 BOM 字符导致 JSON 解析报错，属测试工具伪信号，改用 subprocess + 标准 JSON-RPC 握手后通过。
- 备注：后续若需升级到 mcp 2.0 生态，可迁移到独立维护的 FastMCP 包并改用新 API，属于可选优化，不影响当前架构。

### 下一步计划
- 步骤 2：模块化重构（拆分为 server.py / registry.py / client.py / utils.py，引入工具工厂消除重复）。

---
