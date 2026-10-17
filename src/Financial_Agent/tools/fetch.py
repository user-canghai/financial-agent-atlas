from __future__ import annotations

import re

import requests


def fetch_text(url: str, timeout: int = 30) -> str:
    response = requests.get(
        url,
        timeout=timeout,
        headers={"User-Agent": "Financial-Agent-AtlasServer/0.1"},
    )
    response.raise_for_status()
    text = response.text
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


__all__ = ["fetch_text"]
