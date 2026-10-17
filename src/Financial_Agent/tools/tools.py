from __future__ import annotations

import logging
from pathlib import Path

import requests
from langchain_core.tools import tool

from Financial_Agent.config import Config

logger = logging.getLogger(__name__)


@tool
def web_search(query: str, count: int = 5, summary: bool = True) -> str:
    """使用博查（Bocha）Web Search API 进行联网搜索。

    Args:
        query: 搜索关键词。
        count: 返回结果数量，默认 5。
        summary: 是否返回摘要，默认 True。

    Returns:
        格式化的搜索结果；失败时返回错误说明。
    """
    api_key = Config.get_bocha_api_key()
    if not api_key or api_key.startswith("sk-your-"):
        return "搜索失败：未配置 BOCHA_API_KEY，请在 .env 中填写博查 API Key。"

    payload = {
        "query": query,
        "freshness": "noLimit",
        "summary": summary,
        "count": count,
    }
    try:
        response = requests.post(
            "https://api.bochaai.com/v1/web-search",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30,
        )
    except requests.RequestException as exc:
        return f"搜索失败：网络请求异常 {exc}"

    if response.status_code != 200:
        return f"搜索失败：HTTP {response.status_code}，{response.text[:300]}"

    try:
        body = response.json()
    except ValueError:
        return "搜索失败：响应不是合法 JSON。"

    if body.get("code") not in (200, "200", None):
        return f"搜索失败：{body.get('msg') or body.get('message') or '未知错误'}"

    try:
        pages = body["data"]["webPages"]["value"]
    except (KeyError, TypeError):
        return "搜索失败：响应结构不符合预期。"

    if not pages:
        return "未找到相关结果。"

    lines: list[str] = []
    for index, page in enumerate(pages, start=1):
        lines.append(
            "\n".join(
                [
                    f"引用: {index}",
                    f"标题: {page.get('name', '')}",
                    f"URL: {page.get('url', '')}",
                    f"摘要: {page.get('summary', '')}",
                    f"网站名称: {page.get('siteName', '')}",
                    f"发布时间: {page.get('dateLastCrawled', '')}",
                ]
            )
        )
    return "\n\n".join(lines)


@tool
def database_search(query: str = "") -> str:
    """检索公司的基本财务信息（Mock 数据库）。"""
    return """【2024 年度财务概况】
--------------------------------
公司名称: 深空智能 (DeepSky AI)
总营收 (Total Revenue): 5.2 亿美元
净利润 (Net Profit): 1.2 亿美元
运营成本 (Operating Expenses): 3.5 亿美元
研发投入 (R&D): 8000 万美元
现金储备: 2.1 亿美元
--------------------------------
数据来源: 内部核心数据库 (Mock)"""


@tool
def get_company_profile(company_name: str = "") -> str:
    """获取公司的基础档案信息（Mock）。"""
    return """【公司基础档案】
--------------------------------
公司全称: 深空智能科技有限公司 (DeepSky AI Tech)
成立时间: 2021 年
创始人/CEO: 李未来 (Dr. Future Li)
总部地址: 中国杭州市余杭区人工智能小镇 88 号
员工人数: 约 850 人
核心业务: 通用人工智能 (AGI) 研发、企业级智能 Agent 解决方案
企业愿景: 让智能触手可及
官方网站: www.deepsky-ai.mock
--------------------------------"""


@tool
def get_weather(city: str = "北京") -> str:
    """获取指定城市的天气信息（Mock）。

    Args:
        city: 城市名称，默认北京。
    """
    conditions = ["晴朗", "多云", "小雨", "阴天"]
    index = sum(ord(char) for char in city) % len(conditions)
    temperature = 18 + (sum(ord(char) for char in city) % 13)
    return f"{city} 今日天气：{conditions[index]}，温度 {temperature}°C"


@tool
def read_mcp_resource(server_name: str, resource_uri: str) -> str:
    """读取 MCP 服务器提供的资源（只读）。

    Args:
        server_name: MCP 服务器别名，例如 ``gold_server``。
        resource_uri: 资源 URI，例如 ``account://status``。

    Returns:
        资源文本；失败时返回错误说明。
    """
    from Financial_Agent.mcp.manager import get_manager

    return get_manager().read_resource_sync(server_name, resource_uri)


@tool
def generate_image(
    prompt: str,
    negative_prompt: str = " ",
    size: str = "",
    output_filename: str = "generated_image",
    subfolder: str = "pic",
) -> str:
    """调用 DashScope ImageSynthesis 生成图片并保存到工作区。

    Args:
        prompt: 图像描述，越详细越好。
        negative_prompt: 负面提示词。
        size: 尺寸，格式 ``宽*高``；为空时读取 ``IMAGE_SIZE_DEFAULT``。
        output_filename: 输出文件名（可含扩展名，不含路径）。
        subfolder: ``workspaces`` 下的子目录，默认 ``pic``。

    Returns:
        生成结果与文件路径；失败时返回错误说明。
    """
    api_key = Config.get_qwen_api()
    if not api_key or api_key.startswith("sk-your-"):
        return "图像生成失败：未配置 QWEN_API。"

    size = size or Config.get_image_size()
    valid_sizes = {"1024*1024", "1280*720", "720*1280", "1664*928"}
    if size not in valid_sizes:
        return f"图像生成失败：不支持的尺寸 {size}，可选 {', '.join(sorted(valid_sizes))}。"

    try:
        from dashscope import ImageSynthesis
    except ImportError:
        return "图像生成失败：未安装 dashscope。"

    safe_name = Path(output_filename or "generated_image").name
    if not Path(safe_name).suffix:
        safe_name += ".png"

    output_dir = (Config.get_workspace_dir() / subfolder).resolve()
    workspace_root = Config.get_workspace_dir().resolve()
    if workspace_root not in output_dir.parents and output_dir != workspace_root:
        return "图像生成失败：输出目录越界。"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / safe_name

    image_model = Config.get_image_model()
    print("\n[ImageGenerator] 正在调用图像生成工具...")
    print(f"   尺寸: {size}")
    print(f"   提示词: {prompt[:80]}{'...' if len(prompt) > 80 else ''}")
    print(f"   输出文件: {safe_name}")
    print("\n   正在等待图像生成，请稍候...\n")

    style_prefix = (
        "请生成一张经济学/金融学术严谨风格的信息图：横版 16:9 构图，"
        "信息精简，突出关键词与核心概念，专业、现代、极简，蓝金配色。\n"
    )
    try:
        response = ImageSynthesis.call(
            api_key=api_key,
            model=image_model,
            prompt=style_prefix + prompt,
            negative_prompt=negative_prompt,
            n=1,
            size=size,
            prompt_extend=True,
            watermark=False,
        )
    except Exception as exc:
        return f"图像生成失败：{exc}"

    if getattr(response, "status_code", None) != 200:
        return (
            "图像生成失败："
            f"status_code={getattr(response, 'status_code', 'unknown')}, "
            f"code={getattr(response, 'code', 'unknown')}, "
            f"message={getattr(response, 'message', 'unknown')}"
        )

    results = getattr(getattr(response, "output", None), "results", None) or []
    if not results:
        return "图像生成失败：接口未返回图片。"

    try:
        image_url = results[0].url
        image_bytes = requests.get(image_url, timeout=Config.get_image_timeout()).content
        output_path.write_bytes(image_bytes)
    except Exception as exc:
        return f"图像生成失败：下载图片时出错 {exc}"

    relative_path = output_path.relative_to(Config.get_root_dir())
    return (
        "图像生成成功！\n"
        f"文件路径: {output_path}\n"
        f"相对路径: ./{relative_path.as_posix()}\n"
        f"下载 URL: {image_url}\n"
        f"提示词: {prompt}"
    )


__all__ = [
    "web_search",
    "database_search",
    "get_company_profile",
    "get_weather",
    "read_mcp_resource",
    "generate_image",
]
