# 项目目标文档

## 项目愿景
将 UniChemicals MCP Server 发展为多数据库化学查询的统一 MCP 服务：v1.0.0 在保留 PubChem 能力的基础上，接入 SciFinder（CAS）官方 API 的化学查询能力（API key 鉴权），最终形成 `src/pubchem` 与 `src/cas` 双包结构。

## 背景与动机
v0.3.0 已完成 PubChemPy 能力的重构与扩展（语义化命名、3D 结构/光谱/描述符等）。用户希望启动 v1.0.0 开发：将 SciFinder 的化学查询功能加入本项目，查询需通过 API key 鉴权；测试 key 已放入 `.env` 的 `CAS_COMMON_CHEMISTRY_API_KEY`。同时要求以 `reference-projects` 下两个官方参考项目（CAS-Integration-API、scifinder-api）为示例，挖掘该 API key 能实现的全部功能并接入 MCP server；最终交付结构为 `src` 下存在 `pubchem` 与 `cas` 两个包（需评估 `pubchem_mcp_server` 重命名带来的影响）。

## 核心目标
1. 以 `reference-projects` 两个官方参考项目为依据，挖掘 SciFinder/CAS 官方 API 通过 API key 可实现的全部化学查询功能。
2. 新增 `cas` 包，将上述能力封装为语义化 MCP 工具（沿用 `{数据库}_{动作}_{实体}_by_{标识符}` 命名规范，数据库前缀为 `cas`），鉴权从 `.env` 的 `CAS_COMMON_CHEMISTRY_API_KEY` 读取。
3. 完成目录重组：`src` 下形成 `pubchem`（由 `pubchem_mcp_server` 重命名）与 `cas` 两个包，并全面处理重命名对 pyproject 入口、hatch 打包路径、import 语句、文档与既有脚本引用造成的影响。
4. 版本升至 v1.0.0，构建（`uv build`）、本地 MCP 启动验证与文档（README / README_zh）同步更新。
5. API key 安全处理：仅通过环境变量/.env 注入，不硬编码、不进入提交内容，任何输出不得泄露 key 值。

## 目标用户
需要同时查询 PubChem 与 SciFinder/CAS 化学数据的 AI 助手用户与开发者（通过 MCP 客户端接入），以及希望用统一 MCP 服务完成化学检索的科研、研发人员。

## 期望成果
v1.0.0 交付：MCP server 同时提供 `pubchem` 与 `cas` 两族工具；`cas` 工具覆盖官方参考项目所能演示的 API 查询能力；项目可正常构建并被 MCP 客户端调用；API key 通过 `.env` 安全注入。

## 成功标准
- `src` 下存在 `pubchem` 与 `cas` 两个包，`pubchem_mcp_server` 重命名影响已全部处理（构建、入口、import、文档、脚本均可正常工作）。
- `cas` 工具族覆盖 `reference-projects` 两个官方示例（CAS-Integration-API、scifinder-api）所能演示的 API 能力，且使用 `.env` 的 `CAS_COMMON_CHEMISTRY_API_KEY` 鉴权调用成功。
- 项目 `uv build` 成功；MCP server 可本地启动并被客户端调用，`pubchem` 与 `cas` 工具均可见可用。
- 版本号与文档（README / README_zh）更新至 v1.0.0；API key 未出现在任何提交文件或日志中。

## 范围界定
### 包含
- SciFinder/CAS 官方 API 能力挖掘（以 `reference-projects` 两个官方项目为权威示例，含 Substance / Document / Markush 等模块，具体以参考项目为准）
- `cas` 包实现与 MCP 工具封装（API key 鉴权）
- `src` 目录重组为 `pubchem` + `cas`（`pubchem_mcp_server` → `pubchem` 重命名及其影响处理）
- 构建、测试、文档与版本升级至 v1.0.0
- API key 安全实践（`.env` 读取、gitignore、不泄露）

### 排除
- 超出 CAS 官方 API 能力范围的自研查询功能
- 与化学查询无关的功能
- 移除既有 PubChem 能力（v0.3.0 能力保留并随重命名迁移至 `src/pubchem`）

## 约束条件
- 测试 API key 仅存于 `.env` 的 `CAS_COMMON_CHEMISTRY_API_KEY`；任何文档、对话、提交与日志都不得泄露 key 值。
- `reference-projects` 仅作官方示例参考，尊重其许可证与版权，不整体复制其代码；引用其能力清单时需在规划阶段做许可证兼容性评估。
- 保留用户既有改动（如 `.gitignore` 未提交修改）与 v0.3.0 已有功能。
- MCP 工具沿用语义化命名规范（数据库前缀区分 `pubchem` / `cas`）。
- 最终结构必须是 `src/pubchem` 与 `src/cas` 并存。
- 时间无紧迫要求，但功能挖掘需以官方参考项目为准，保证覆盖面。

## 澄清问答记录
<!-- GOAL-QA-LOG-START -->

### QA-R001：源码整理与功能增加的目标、范围与约束
<!-- GOAL-QA-R001-START -->
- **提问时间**：2026-08-06 14:45
- **提问目的**：用户提出「对源码进行整理和功能增加」，意图方向较宽。先明确核心成果、功能范围和限制条件，才能形成可实施的目标文档。
- **问题列表**
  1. 这次「源码整理 + 功能增加」最想达成的核心成果是什么？（例如：修正打包问题、优化代码结构、新增查询能力，或兼而有之？）
  2. 功能增加覆盖哪些方向？哪些明确不做？（例如：补充现有工具族、新增 3D 结构/光谱/描述符等数据类型、批量下载、缓存优化……）
  3. 有哪些约束条件？（例如：Python 版本、是否必须保持 AGPL+商业限制许可证、是否要求兼容现有 MCP 工具名、交付时间等）
- **用户回答**
  1. 兼而有之
  2. 补充现有工具族、新增 3D 结构/光谱/描述符等数据类型
  3. 不做下载工具，对MCP工具采用语义化命名
- **提炼结论**
  - 核心成果 = 打包修正 + 代码重构 + 功能扩充，三者并行。
  - 功能方向聚焦：现有工具族补齐 + 新增 3D/光谱/描述符数据类型。
  - 下载工具明确排除，但现有 download_* 工具的去留需进一步确认。
  - 命名规范改为语义化命名，可能涉及现有工具重命名，兼容策略需进一步确认。
- **影响的目标文档章节**
  - 核心目标 / 范围界定 / 约束条件 / 成功标准
<!-- GOAL-QA-R001-END -->

### QA-R002：下载工具去留、命名兼容策略与成功标准
<!-- GOAL-QA-R002-START -->
- **提问时间**：2026-08-06 14:55
- **提问目的**：QA-R001 的回答中，有两处直接影响范围界定与兼容性的关键点需要确认（现有下载工具怎么处理、语义化命名是否重命名现有工具），同时补齐成功标准与时间约束。
- **问题列表**
  1. 现有 6 个 `download_by_*` 工具怎么处理？（a. 全部移除；b. 保留不动但不再新增；c. 保留并重命名成语义化名称）
  2. 语义化命名是否会对现有工具全部重命名？是否要保留旧名称作为别名，兼容已接入的 MCP 客户端？
  3. 这次改造的「成功」如何判断？有没有时间预期？（例如：必须能 `uv build` 成功并在本地跑通；预计何时交付）
- **用户回答**
  1. 现有 6 个 `download_by_*` 工具全部移除。
  2. 采用 `pubchem_search_compound_by_cid` 风格：命名必须包含来自哪个数据库（pubchem）、搜索什么（compound）、依靠什么搜索（cid）；考虑后续可能接入其他数据库。
  3. 成功标准：必须 `uv build` 成功，并且跑通基于 `uvx` 的远程 MCP 服务；时间上慢慢来。
- **提炼结论**
  - 下载工具族整体移除，代码与 README 等文档需同步清理。
  - 命名规范确立为 `{数据库}_{动作}_{实体}_by_{标识符}`，预留多数据库扩展。
  - 成功标准明确：可构建 + 可通过 uvx 远程运行。
  - 无时间压力。
- **影响的目标文档章节**
  - 范围界定 / 约束条件 / 成功标准
<!-- GOAL-QA-R002-END -->

### QA-R003：目标用户与发布方式、工具族补充的具体方向、目标完整性确认
<!-- GOAL-QA-R003-START -->
- **提问时间**：2026-08-06 14:58
- **提问目的**：目标文档主体已基本成型，最后确认使用/发布对象、工具族补充的具体含义，并确认是否还有其他目标，以便整理最终目标文档。
- **问题列表**
  1. 这个 MCP 服务器计划公开发布到 PyPI（供社区通过 uvx 使用），还是仅内部/个人使用？许可证是否维持 AGPL + 商业使用限制？
  2. 「补充现有工具族」具体指什么？例如：支持按多个 CID/SMILES 批量查询、支持返回条数限制/分页，还是你心里已有具体清单？
  3. 除了上述内容，还有其他想实现的目标吗？若没有，下一轮我将整理最终目标文档。
- **用户回答**
  1. 公开发布到 PyPI；许可证修改为 GNU 许可，即"有传染性、无授权禁止商用"。
  2. 尽可能挖掘 pubchempy 包，看看其本身具有的功能哪些可以加入。
  3. 无其他目标。
- **提炼结论**
  - 目标用户 = 公开社区用户 + AI 助手使用者；发布渠道 = PyPI。
  - 功能方向 = 全面覆盖 PubChemPy 能力。
  - 许可证表述存在歧义：标准 GNU（GPL/AGPL）允许商用，与"无授权禁止商用"不完全等价，需 QA-R004 澄清。
- **影响的目标文档章节**
  - 目标用户 / 期望成果 / 范围界定 / 核心目标
<!-- GOAL-QA-R003-END -->

### QA-R004：许可证具体条款确认
<!-- GOAL-QA-R004-START -->
- **提问时间**：2026-08-06 15:01
- **提问目的**：用户表述「GNU 许可 = 有传染性 + 无授权禁止商用」与标准 GNU 许可证（GPL/AGPL 允许商用、仅要求遵守开源义务）不完全一致。许可证影响公开发布与授权方式，需要确认具体选择，避免目标文档失真。
- **问题列表**
  1. 许可证具体选哪种？（a. 标准 GPL-3.0 或 AGPL-3.0：具传染性，商用需遵守开源义务即可；b. 保持「GPL/AGPL + 商业使用限制附加条款」：商用需单独授权，即你描述的"无授权禁止商用"；c. 其他自定义条款）
- **用户回答**
  1. 改用 PolyForm Noncommercial License 1.0.0。
- **提炼结论**
  - 用户选定 PolyForm Noncommercial 1.0.0。
  - 该许可证禁止商用（商用必须另行授权）✓，但**不具传染性**（无 share-alike、无源码公开义务）✗，与最初「有传染性 + 无授权禁止商用」的诉求不完全吻合。
  - 是否接受该取舍，需 QA-R005 确认。
- **影响的目标文档章节**
  - 约束条件
<!-- GOAL-QA-R004-END -->

### QA-R005：是否接受 PolyForm Noncommercial 的"禁止商用但不传染"特性
<!-- GOAL-QA-R005-START -->
- **提问时间**：2026-08-06 15:16
- **提问目的**：PolyForm Noncommercial 1.0.0 只满足「商用必须授权」，不满足「传染性」。需要用户确认是接受此取舍，还是调整方案以同时满足两个诉求。
- **问题列表**
  1. 许可证方案最终怎么定？（a. 接受 PolyForm Noncommercial 1.0.0（禁止商用、无传染性）；b. 需要同时满足「传染性 + 商用需授权」，则改用「AGPL-3.0 + 商业使用限制附加条款」这类组合；c. 其他方案）
- **用户回答**
  1. 需要 (b)：AGPL-3.0 + 商业使用限制附加条款，同时满足「传染性 + 商用需授权」。
- **提炼结论**
  - 许可证方案确定：主许可证采用 AGPL-3.0（与现有 LICENSE 结构一致），附加商业使用限制条款。
  - 两个诉求「传染性」与「无授权禁止商用」同时满足。
- **影响的目标文档章节**
  - 约束条件
<!-- GOAL-QA-R005-END -->

### QA-R006：v1.0.0 接入 SciFinder/CAS 查询的目标、范围与结构
<!-- GOAL-QA-R006-START -->
- **提问时间**：2026-08-08 13:22
- **提问目的**：用户提出 v1.0.0 开发需求（接入 SciFinder 化学查询功能，API key 鉴权），其中"挖掘该 API key 能实现的全部功能"范围较宽，且涉及目录重命名，需要将成果、功能范围、结构要求与安全约束固化为可实施目标。
- **问题列表**
  1. v1.0.0 的核心交付物是什么？（新增 SciFinder/CAS 查询工具集并重组为 pubchem + cas 双包结构）
  2. `cas` 功能范围如何界定？（以两个官方参考项目为据，挖掘 API key 可实现的全部功能）
  3. 目录结构与重命名影响如何处理？（`src/pubchem` + `src/cas`；`pubchem_mcp_server` 重命名为 `pubchem` 对构建/入口/import/文档的影响）
  4. 鉴权与凭据安全约束？（测试 key 在 `.env` 的 `CAS_COMMON_CHEMISTRY_API_KEY` 下）
- **用户回答**
  1. 对项目进行 v1.0.0 开发，将 SciFinder 的化学查询功能加入本 MCP server，查询需通过 API key。
  2. 通过两个官方参考项目 `reference-projects` 的示例，挖掘该 API key 能实现的全部功能并加入。
  3. 最终交付结构为 `src` 下存在 `pubchem` 与 `cas` 两个文件夹；需要考虑 `pubchem_mcp_server` 重命名可能带来的影响。
  4. 测试用 key 已放在 `.env` 文件夹的 `CAS_COMMON_CHEMISTRY_API_KEY` 下。
- **提炼结论**
  - v1.0.0 = 在现有 PubChem MCP server 基础上接入 CAS/SciFinder 官方 API 化学查询能力，形成多数据库查询服务。
  - `cas` 功能清单以官方参考项目为准全量挖掘：CAS-Integration-API（Substance / Document / Markush 等模块）与 scifinder-api（tutorials / sample-code）。
  - 目标结构确定为 `src/pubchem` 与 `src/cas`；`pubchem` 由 `pubchem_mcp_server` 重命名而来，重命名影响（pyproject 入口、hatch packages、import、文档、既有脚本）纳入 v1.0.0 范围。
  - 凭据安全：仅引用键名 `CAS_COMMON_CHEMISTRY_API_KEY`，任何输出不得泄露 key 值。
  - 待确认点（不阻塞目标交付）：`cas` 工具命名是否严格沿用 pubchem 的语义化规范；API key 的有效期/限流未知；参考项目许可证与本项目许可证（AGPL-3.0 + 商业使用限制）的兼容性需在规划阶段评估。
- **影响的目标文档章节**
  - 核心目标 / 期望成果 / 成功标准 / 范围界定 / 约束条件
<!-- GOAL-QA-R006-END -->

### QA-R007：v1.1.0 收尾：unichemicals 调用一致性收口与 pubchempy 旧包清理
<!-- GOAL-QA-R007-START -->
- **提问时间**：2026-08-09 00:07
- **提问目的**：用户提出两项收尾步骤（1. 修改 readme、mcp.json 等文件，保持调用库为 unichemical；2. 清理掉 pubchempy 的旧包等内容）。v1.1.0 已完成包名与显示名统一，本步骤属于收口；其中「清理 pubchempy 旧包」的范围存在歧义（本地构建产物 / PyPI 旧包 / 文档旧引用 / 第三方依赖），需要先澄清，避免误删第三方依赖 `pubchempy` 导致 PubChem 数据源失效。
- **问题列表**
  1. 步骤 1 的收尾范围：README / README_zh 与 mcp-client-example.json 已改为 `unichemicals-mcp-server`；仓库中没有 `mcp.json` 文件，你指的是 `mcp-client-example.json`（或你 MCP 客户端里实际使用的配置文件）吗？是否还需要把 README 中「基于 PubChemPy 构建」等旧定位描述一并调整？
  2. 步骤 2「清理 pubchempy 旧包」的范围是什么？（a. 仅清理本地 `dist/` 下的旧 wheel/sdist 产物（如 `pubchempy_mcp_server-0.1.1/0.2.0/0.3.0`）；b. 从 PyPI 下架旧包 `pubchempy-mcp-server`（0.3.0 及更早，需你在 PyPI 操作）；c. 清理文档/示例中的旧名引用；d. 其他）
  3. 是否确认**不删除** `pyproject.toml` 中的第三方依赖 `pubchempy>=1.0.5`（它是 PubChem 数据源的工具库，删除会导致 40 个 `pubchem_*` 工具失效）？
- **用户回答**
  1. 步骤 1 所指配置文件就是 `mcp-client-example.json`（仓库中没有其他 mcp.json）。
  2. 只清理本地 `dist/` 下的旧构建产物（`pubchempy_mcp_server-0.1.1/0.2.0/0.3.0` 的 wheel/sdist，已不入库）。
  3. 确保第三方依赖没问题（即保留 `pubchempy>=1.0.5`，不删除）。
- **提炼结论**
  - 步骤 1 范围 = `mcp-client-example.json` 与 README 等面向调用方的文件，调用名统一为 `unichemicals-mcp-server`（v1.1.0 已基本完成，本步骤做收口复核）。
  - 步骤 2 范围 = 仅清理本地 `dist/` 下旧包名（`pubchempy_mcp_server-*`）的构建产物；不含 PyPI 下架、不含历史文档改写。
  - 约束 = 第三方依赖 `pubchempy>=1.0.5` 必须保留并验证可用（PubChem 数据源依赖）。
  - 收尾决策（用户确认）：PyPI 旧包 `pubchempy-mcp-server` **不下架**，保留兼容；README 中「基于 PubChemPy 构建」的定位描述**需要调整**为 UniChemicals 多数据源视角（已同步修改 README / README_zh 致谢段落，PubChemPy 降为“底层依赖库之一”并保留致谢）。
- **影响的目标文档章节**
  - 核心目标 / 范围界定 / 成功标准 / 约束条件
<!-- GOAL-QA-R007-END -->

<!-- GOAL-QA-LOG-END -->

## 备注
- 本文档主章节自 2026-08-08 起反映 v1.0.0 目标（QA-R006）；v0.3.0 周期的目标内容保留在「澄清问答记录」QA-R001 ~ QA-R005 历史中。
- 2026-08-09 新增 QA-R007：v1.1.0 收尾目标（unichemicals 调用一致性收口 + dist 旧构建产物清理 + 第三方依赖保留验证）。
- 参考项目位置：`reference-projects/CAS-Integration-API-main/CAS-Integration-API-main`（Python）与 `reference-projects/scifinder-api-main/scifinder-api-main`（JS/TS 官方示例），均已加入 .gitignore。
- 下一步建议调用 **project-planner-cn** agent 进行 v1.0.0 的实现规划。
