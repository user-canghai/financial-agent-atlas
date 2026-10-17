from __future__ import annotations

from Financial_Agent.skills.base_skill import BaseSkill, SkillResult


class WebSearchSkill(BaseSkill):
    name = "web"
    description = "调用博查搜索获取实时网页资料"
    keywords = ("搜索", "网页", "新闻", "search", "web")

    def execute(self, **kwargs) -> SkillResult:
        from Financial_Agent.tools.tools import web_search

        query = str(kwargs.get("query", "")).strip()
        if not query:
            return SkillResult(False, "缺少 query 参数")
        try:
            content = web_search.invoke(
                {"query": query, "count": int(kwargs.get("count", 5)), "summary": True}
            )
        except Exception as exc:
            return SkillResult(False, f"搜索失败: {exc}")
        success = not str(content).startswith("搜索失败")
        return SkillResult(success, str(content))


__all__ = ["WebSearchSkill"]
