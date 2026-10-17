from __future__ import annotations

import json
from typing import Any

PREVIEW_LIMIT = 320


def _short(value: Any, limit: int = 160) -> str:
    text = str(value).replace("\n", " ")
    return text if len(text) <= limit else text[:limit] + "..."


def format_tool_call(name: str, args: dict[str, Any]) -> list[str]:
    lines = ["", "  工具调用", f"m  {name}"]
    if name == "task":
        lines.append(f"   subagent_type: {args.get('subagent_type', '')}")
        lines.append(f"   任务: {_short(args.get('description', ''), 300)}")
        return lines
    if name == "read_mcp_resource":
        lines.append(f"   server_name: {args.get('server_name', '')}")
        lines.append(f"   resource_uri: {args.get('resource_uri', '')}")
        return lines
    if name in {"web_search", "database_search"}:
        if "query" in args:
            lines.append(f"   query: {_short(args['query'], 200)}")
        for key, value in args.items():
            if key != "query":
                lines.append(f"   {key}: {_short(value)}")
        return lines
    if name == "generate_image":
        lines.append(f"   output_filename: {args.get('output_filename', '')}")
        lines.append(f"   size: {args.get('size', '')}")
        lines.append(f"   prompt: {_short(args.get('prompt', ''), 240)}")
        return lines
    if name in {"write_file", "edit_file"}:
        lines.append(f"   path: {args.get('file_path', args.get('path', ''))}")
        if "content" in args:
            lines.append(f"   content: {_short(args['content'], 200)}")
        return lines
    for key, value in args.items():
        lines.append(f"   {key}: {_short(value)}")
    return lines


def format_tool_result(name: str, content: Any) -> list[str]:
    text = str(content) if content is not None else ""
    lines = [f"✓ [{name}] 完成"]
    if text.strip():
        preview = text.strip()
        if len(preview) > PREVIEW_LIMIT:
            preview = preview[:PREVIEW_LIMIT] + "..."
        lines.append("   预览: " + preview.replace("\n", "\n         "))
    return lines


def format_json(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, indent=2)
    except TypeError:
        return str(value)


__all__ = ["format_tool_call", "format_tool_result", "format_json"]
