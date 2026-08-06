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
