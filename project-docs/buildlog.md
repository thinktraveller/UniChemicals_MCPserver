# 构建日志

## [2026-08-08] v1.0.0 构建记录（步骤 8–13：CAS Common Chemistry 接入）

### 补充记录：MCP 客户端 JSON 接入示例（2026-08-08 16:33）

- 新增 `mcp-client-example.json`：可直接导入 MCP 客户端的 `mcpServers` 配置（命令 `uvx --refresh pubchempy-mcp-server`），`env` 中提供 `CAS_COMMON_CHEMISTRY_API_KEY` 占位符，供 Cherry Studio / claude_desktop_config.json 等客户端使用。
- README.md / README_zh.md 的「MCP client configuration」章节同步更新：引用该示例文件，说明 key 替换方式、不支持 `env` 的客户端改用系统环境变量、以及仅用 PubChem 工具时可移除 `env` 块。
- 安全说明：示例中仅含 `your_api_key_here` 占位符，无真实 key 值入库。

### 步骤 8：官方文档核对与 API 只读探测

#### 执行的任务
- 通读用户提供的官方文档 `reference-projects/CAS 常用化学 --- CAS Common Chemistry (2026_8_8 13：49：16).html`（OAS 2.0 页面），固化三端点规格：`GET /search`（q/offset/size）、`GET /detail`（cas_rn 或 uri）、`GET /export`（uri/returnAsAttachment），鉴权头 `X-Api-Key`，Base URL `https://commonchemistry.cas.org/api`。
- 使用 `.env` 中测试 key 做 5 轮只读 GET 探测（探测脚本仅本地运行于 `%TEMP%`，未入库；全程未输出 key 值）。

#### 实测结论（与官方文档的差异，已作为实现依据）
| 项目 | 官方文档描述 | 实测行为 |
|---|---|---|
| `/search` 结果字段 | `results[].image` | 实际为 `results[].images`（SVG 字符串数组，通常 1 个） |
| `/search` 的 `count` | 字符串 | 实际为整数 |
| InChIKey 搜索 | 文档称支持 | 实测**必须带 `InChIKey=` 前缀**，裸 InChIKey 返回 0 结果；工具层已自动补前缀 |
| InChI 搜索 | 带/不带 `InChI=` 均可 | 实测两种形式均可（工具层不做强制转换） |
| `/detail.inchiKey` | 裸 InChIKey | 实际带 `InChIKey=` 前缀 |
| `/detail.smile` | 字段存在 | 实测多为空串，`canonicalSmile` 有值 |
| `/detail.molecularFormula` / 名称 | 纯文本 | 实际含 HTML 标记（`<sub>`、`<em>`），工具层已剥离 |
| `/detail` 额外字段 | 文档未列 | `hasMolfile`（布尔）、`images`（SVG 数组） |
| `/export` URI | 文档示例 `substance/pt/50000` | 必须使用 `/detail` 返回的精确 uri（水为 `substance/pt/7732185`），自行拼接会 404 |
| 分页上限 | 每页最多 100 | 实测 `size=500` 仍返回 100；`size=0` 返回空 results（HTTP 200）；`size<0` 触发 500 |
| 鉴权 | `X-Api-Key` | 大小写不敏感（`X-API-KEY` 亦有效）；无 key 或错误 key 返回 403 `{"message": "API key required..."}` |
| 错误码 | 400/404/500 | 实测一致；404 返回 `{"message": "Detail not found"}`，400 为 `Missing required parameter: q` |

- key 有效性：测试 key 有效（40 字符），三端点全部调用成功，无 401/403/429。

### 步骤 9：`src/pubchem_mcp_server` → `src/pubchem` 重命名

- `git mv src/pubchem_mcp_server src/pubchem`，全仓引用核对：包内均为相对导入，无绝对导入残留；`pyproject.toml` 入口更新为 `pubchem.server:main`、hatch packages 更新为 `["src/pubchem", "src/cas"]`；`client.py` 的 PUG-View User-Agent 更新为 `unichemicals-mcp-server/1.0`。
- 工具数量校正：v0.3.0 最终验收实际为 **40** 个 `pubchem_*` 工具（开发期 buildlog 曾记 41，属早期计数误差），计划书已同步修正为 40。

### 步骤 10：`cas` 包骨架与鉴权客户端

- 新增 `src/cas/{__init__,client,utils,registry}.py`；`client.py` 封装 `.env` 读取（`CAS_COMMON_CHEMISTRY_API_KEY`）、`X-Api-Key` 注入、30s 超时、429/5xx 指数退避重试、错误归一化（400/403/404/429/5xx → 友好中文消息）。
- `pyproject.toml` 新增依赖 `python-dotenv>=1.0`，版本升至 `1.0.0`。
- 未配置 key 时返回明确 `Error: 环境变量 CAS_COMMON_CHEMISTRY_API_KEY 未配置...`，不打印 key 值。

### 步骤 11：`cas` 工具实现与注册（11 个工具）

- 5 个搜索（共用 `/search`）：`cas_search_substance_by_name`（尾部通配符）、`by_casrn`、`by_smiles`、`by_inchi`、`by_inchikey`（自动补前缀）；均含 offset/size 校验（size 1~100）。
- 2 个详情：`cas_get_substance_by_casrn`、`cas_get_substance_by_uri`。
- 2 个 molfile：`cas_get_molfile_by_uri`（直取 `/export`）、`cas_get_molfile_by_casrn`（detail→uri→export 两段封装，hasMolfile=false 时友好报错）。
- 2 个便捷提取：`cas_get_properties_by_casrn`、`cas_get_image_by_casrn`。
- MCP 工具层真实调用验证：11/11 全部成功（甲醛 50-00-0、水 7732-18-5 molfile、InChIKey/InChI/SMILES/名称搜索、404 友好错误）；pubchem 工具无回归。

### 步骤 12：双库统一注册、版本 1.0.0、依赖与文档

- `server.py` 双库注册（pubchem 40 + cas 11 = 51），服务名改为 `UniChemicals_MCP_Server`。
- 新增 `.env.example`（仅占位符）；README.md / README_zh.md 新增 CAS 章节（配置、11 工具清单、数据政策），工具总数更新为 51。

### 步骤 13：端到端验收与安全审计

- `uv build` 成功：`dist/pubchempy_mcp_server-1.0.0-py3-none-any.whl` + `.tar.gz`；wheel 含 `pubchem/server.py` 与 `cas/{client,registry}.py`；entry point = `pubchem.server:main`；METADATA Version 1.0.0、License AGPL-3.0-only、Requires-Dist 含 python-dotenv。
- stdio MCP 握手：initialize → tools/list 返回 51 工具（40 pubchem + 11 cas），`serverInfo` = UniChemicals_MCP_Server。
- 结构：`src` 下仅 `pubchem` 与 `cas` 两个目录。
- 安全审计：`git grep` 无 key 值（仅键名与占位符）；`.env`、`reference-projects`、`dist`、`.venv` 均被 .gitignore 忽略未入库。
- 遗留提示：测试 key 曾在早期探测输出中短暂出现（未入库、未进日志），建议使用后轮换。

---

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

## [2026-08-07 02:06] 步骤 7 进行中：版本升至 0.3.0，本地端到端验证通过（待 PyPI 发布）

### 执行的任务
- 用户确认：PyPI 包名 `pubchempy-mcp-server` 未被占用，且 0.2.0 已由用户此前发布过，本次构建打包为 **0.3.0**（`uv publish` 由用户执行）。
- 版本号统一升至 0.3.0：`pyproject.toml`（version）+ `client.py`（PUG-View User-Agent）；
- 清理 dist 中 0.2.0 旧产物，`uv build` 成功生成 0.3.0 wheel + sdist；
- 发布前最终端到端验证（MCP 握手 + 联网真实调用）全部通过。

### 关键变更
- `pyproject.toml`：`version = "0.3.0"`
- `src/pubchem_mcp_server/client.py`：`PUG_VIEW_USER_AGENT` → `pubchempy-mcp-server/0.3`
- `dist/pubchempy_mcp_server-0.3.0-py3-none-any.whl` / `.tar.gz`（gitignore，不入库）

### 验证结果
- 0.3.0 wheel METADATA：`Version: 0.3.0`、`License-Expression: AGPL-3.0-only`、`Requires-Python: >=3.10`、依赖 `mcp[cli]<2.0,>=1.0.0` / `pandas>=2.0.0` / `pubchempy>=1.0.5` / `requests>=2.31`；
- 最终端到端：`tools/list` 40 个工具（全部 `pubchem_*` 前缀）；search / batch / conformer / descriptor / spectrum 五个关键工具真实调用全部 `isError=False`，服务退出码 0。

### 遇到的问题及解决方案
- 无。版本号策略已按用户确认调整为 0.3.0（避免与已发布的 0.2.0 冲突）。

### 下一步计划
- 用户执行 `uv publish` 发布 0.3.0 到 PyPI；
- 发布完成后，用 `uvx --refresh pubchempy-mcp-server` 在独立环境验证远程 MCP 服务（工具列表 40 个一致、真实调用正常），然后写入构建完成标记。

---

## [2026-08-08 12:40] 🎉 项目构建完成

### 完成情况
- 用户已执行 `uv publish` 将 0.3.0 发布到 PyPI；
- 独立环境验收（`uvx --refresh pubchempy-mcp-server`，从 PyPI 拉取 48 个包）通过：
  - `tools/list` 返回 40 个工具，全部为 `pubchem_*` 语义化命名；
  - `pubchem_get_spectrum_by_cid` 等新工具在列；
  - 真实调用 `pubchem_search_compound_by_cid(2244)` 正常返回（`isError=False`），服务退出码 0；
- 成功标准达成：`uv build` 成功 + 基于 `uvx` 的远程 MCP 服务跑通（可被 MCP 客户端正常调用）。

### 验收记录
- PyPI 包：`pubchempy-mcp-server` 0.3.0（`https://pypi.org/project/pubchempy-mcp-server/`）；
- wheel 元数据：`License-Expression: AGPL-3.0-only`、`Requires-Python: >=3.10`、依赖 `mcp[cli]>=1.0.0,<2.0` / `pubchempy>=1.0.5` / `pandas>=2.0.0` / `requests>=2.31`；
- 已知无害警告：mcp SDK 启动时输出 `pydantic_settings IncompleteFieldDefinitionWarning (lifespan)`，属上游库字段类型提示，不影响功能。

### 最终交付审计
- `project-docs/` 下本构建流程仅创建/修改 `buildlog.md`（未触碰 goal.md / project-plan.md / teach.md）；
- 全部 7 个步骤均已记录完成情况、验证结果与问题处理；
- 每次提交均显式列出文件路径，无 `_verify/` 脚本、无密钥、无构建产物入库；
- 全部提交均在本仓库本地完成，`git push` 未执行（用户未授权）。

### 下一步计划
- ✅ 构建已全部完成，无待执行步骤。可进入「使用」阶段：在 MCP 客户端配置 `uvx --refresh pubchempy-mcp-server` 即可接入。

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
