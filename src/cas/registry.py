"""Tool registry for the CAS Common Chemistry API.

Tools follow the convention ``{database}_{action}_{entity}_by_{identifier}``
with database prefix ``cas``, mirroring the pubchem package.
"""

from typing import Any, Callable

from . import client
from .utils import safe_execute


def _search_by_name(name: str, offset: int = 0, size: int = 10) -> str:
    return safe_execute(client.search, name, offset=offset, size=size)


def _search_by_casrn(cas_rn: str, offset: int = 0, size: int = 10) -> str:
    return safe_execute(client.search, cas_rn, offset=offset, size=size)


def _search_by_smiles(smiles: str, offset: int = 0, size: int = 10) -> str:
    return safe_execute(client.search, smiles, offset=offset, size=size)


def _search_by_inchi(inchi: str, offset: int = 0, size: int = 10) -> str:
    return safe_execute(client.search, inchi, offset=offset, size=size)


def _search_by_inchikey(inchikey: str, offset: int = 0, size: int = 10) -> str:
    return safe_execute(client.search, inchikey, offset=offset, size=size)


def _make_detail_tool(by_uri: bool) -> Callable[..., str]:
    if by_uri:
        doc = (
            "按 URI 获取 CAS Common Chemistry 物质完整详情。\n\n"
            "- uri: 物质 URI（来自 search 结果或 detail 响应），如 substance/pt/50000\n\n"
            "返回完整详情 JSON（uri/rn/name/inchi/inchiKey/canonicalSmile/molecularFormula/"
            "molecularMass/experimentalProperties/propertyCitations/synonyms/replacedRns/images 等），"
            "或 Error: <message>。"
        )

        def tool_uri(uri: str) -> str:
            return safe_execute(client.detail, uri=uri)

        tool_uri.__name__ = "cas_get_substance_by_uri"
        tool_uri.__doc__ = doc
        return tool_uri

    doc = (
        "按 CAS 登记号（RN）获取 CAS Common Chemistry 物质完整详情。\n\n"
        "- cas_rn: CAS 登记号，如 50-00-0\n\n"
        "返回完整详情 JSON（uri/rn/name/inchi/inchiKey/canonicalSmile/molecularFormula/"
        "molecularMass/experimentalProperties/propertyCitations/synonyms/replacedRns/images 等），"
        "或 Error: <message>。"
    )

    def tool_casrn(cas_rn: str) -> str:
        return safe_execute(client.detail, cas_rn=cas_rn)

    tool_casrn.__name__ = "cas_get_substance_by_casrn"
    tool_casrn.__doc__ = doc
    return tool_casrn


def _make_molfile_tool(by_uri: bool) -> Callable[..., str]:
    if by_uri:
        doc = (
            "按 URI 获取 CAS Common Chemistry 物质的 molfile（V2000 文本）。\n\n"
            "- uri: 物质 URI（必须来自 /detail 响应，实测不可自行拼接），如 substance/pt/50000\n\n"
            "返回 molfile 文本，或 Error: <message>。"
        )

        def tool_uri(uri: str) -> str:
            return safe_execute(client.export, uri)

        tool_uri.__name__ = "cas_get_molfile_by_uri"
        tool_uri.__doc__ = doc
        return tool_uri

    doc = (
        "按 CAS 登记号（RN）获取物质的 molfile（V2000 文本）。\n\n"
        "- cas_rn: CAS 登记号，如 50-00-0\n\n"
        "内部先调用 /detail 取真实 uri，再调用 /export 导出 molfile；"
        "若物质没有 molfile（hasMolfile=false）返回明确错误。\n"
        "返回 molfile 文本，或 Error: <message>。"
    )

    def tool_casrn(cas_rn: str) -> str:
        return safe_execute(client.export_by_casrn, cas_rn)

    tool_casrn.__name__ = "cas_get_molfile_by_casrn"
    tool_casrn.__doc__ = doc
    return tool_casrn


def _make_properties_tool() -> Callable[..., str]:
    doc = (
        "按 CAS 登记号（RN）提取物质的实验性质与性质引用（基于 /detail 响应，非独立端点）。\n\n"
        "- cas_rn: CAS 登记号，如 50-00-0\n\n"
        "返回 {rn, name, experimentalProperties[], propertyCitations[]}，"
        "字段缺失时返回明确提示，或 Error: <message>。"
    )

    def tool(cas_rn: str) -> str:
        def _extract() -> dict:
            data = client.detail(cas_rn=cas_rn)
            props = data.get("experimentalProperties") or []
            citations = data.get("propertyCitations") or []
            if not props and not citations:
                raise ValueError(f"CAS RN {cas_rn} 没有实验性质或性质引用数据")
            return {
                "rn": data.get("rn"),
                "name": data.get("name"),
                "experimentalProperties": props,
                "propertyCitations": citations,
            }

        return safe_execute(_extract)

    tool.__name__ = "cas_get_properties_by_casrn"
    tool.__doc__ = doc
    return tool


def _make_image_tool() -> Callable[..., str]:
    doc = (
        "按 CAS 登记号（RN）获取物质的结构图（SVG，基于 /detail 响应的 images 字段，非独立端点）。\n\n"
        "- cas_rn: CAS 登记号，如 50-00-0\n\n"
        "返回 {rn, name, images[SVG...]}（images 为 SVG 字符串数组），或 Error: <message>。"
    )

    def tool(cas_rn: str) -> str:
        def _extract() -> dict:
            data = client.detail(cas_rn=cas_rn)
            images = data.get("images") or []
            if not images:
                raise ValueError(f"CAS RN {cas_rn} 没有结构图数据")
            return {"rn": data.get("rn"), "name": data.get("name"), "images": images}

        return safe_execute(_extract)

    tool.__name__ = "cas_get_image_by_casrn"
    tool.__doc__ = doc
    return tool


def register_all(mcp: Any) -> None:
    """Register every CAS MCP tool on the given FastMCP instance."""
    _search_by_name.__doc__ = (
        "按名称搜索 CAS Common Chemistry 物质（不区分大小写，支持尾部通配符，如 car*）。\n\n"
        "- name: 物质名称\n- offset: 分页偏移（默认 0）\n- size: 每页条数 1~100（默认 10）\n\n"
        "返回 count 与 results（每项含 rn / name / images[SVG]），或 Error: <message>。"
    )
    _search_by_casrn.__doc__ = (
        "按 CAS 登记号（RN）搜索 CAS Common Chemistry 物质（带或不带连字符均可）。\n\n"
        "- cas_rn: CAS 登记号，如 50-00-0\n- offset: 分页偏移（默认 0）\n- size: 每页条数 1~100（默认 10）\n\n"
        "返回 count 与 results（每项含 rn / name / images[SVG]），或 Error: <message>。"
    )
    _search_by_smiles.__doc__ = (
        "按 SMILES 搜索 CAS Common Chemistry 物质（canonical 或 isomeric）。\n\n"
        "- smiles: SMILES 字符串，如 C=O\n- offset: 分页偏移（默认 0）\n- size: 每页条数 1~100（默认 10）\n\n"
        "返回 count 与 results（每项含 rn / name / images[SVG]），或 Error: <message>。"
    )
    _search_by_inchi.__doc__ = (
        "按 InChI 搜索 CAS Common Chemistry 物质（带或不带 InChI= 前缀均可）。\n\n"
        "- inchi: InChI 字符串，如 InChI=1S/CH2O/c1-2/h1H2\n"
        "- offset: 分页偏移（默认 0）\n- size: 每页条数 1~100（默认 10）\n\n"
        "返回 count 与 results（每项含 rn / name / images[SVG]），或 Error: <message>。"
    )
    _search_by_inchikey.__doc__ = (
        "按 InChIKey 搜索 CAS Common Chemistry 物质（自动补充 InChIKey= 前缀，实测该前缀必需）。\n\n"
        "- inchikey: InChIKey 字符串，如 WSFSSNUMVMOOMR-UHFFFAOYSA-N\n"
        "- offset: 分页偏移（默认 0）\n- size: 每页条数 1~100（默认 10）\n\n"
        "返回 count 与 results（每项含 rn / name / images[SVG]），或 Error: <message>。"
    )
    mcp.tool(name="cas_search_substance_by_name")(_search_by_name)
    mcp.tool(name="cas_search_substance_by_casrn")(_search_by_casrn)
    mcp.tool(name="cas_search_substance_by_smiles")(_search_by_smiles)
    mcp.tool(name="cas_search_substance_by_inchi")(_search_by_inchi)
    mcp.tool(name="cas_search_substance_by_inchikey")(_search_by_inchikey)
    mcp.tool(name="cas_get_substance_by_casrn")(_make_detail_tool(by_uri=False))
    mcp.tool(name="cas_get_substance_by_uri")(_make_detail_tool(by_uri=True))
    mcp.tool(name="cas_get_molfile_by_casrn")(_make_molfile_tool(by_uri=False))
    mcp.tool(name="cas_get_molfile_by_uri")(_make_molfile_tool(by_uri=True))
    mcp.tool(name="cas_get_properties_by_casrn")(_make_properties_tool())
    mcp.tool(name="cas_get_image_by_casrn")(_make_image_tool())
