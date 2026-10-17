from __future__ import annotations

from Financial_Agent.skills.base_skill import BaseSkill, SkillResult


class GoldAnalysisSkill(BaseSkill):
    name = "gold"
    description = "读取黄金账户状态并计算总资产"
    keywords = ("黄金", "金价", "Au99.99", "gold")

    def execute(self, **kwargs) -> SkillResult:
        from Financial_Agent.mcp.manager import get_manager

        price = kwargs.get("price")
        status = get_manager().read_resource_sync("gold_server", "account://status")
        if status.startswith("读取 MCP 资源失败"):
            return SkillResult(False, status)

        content = status
        if price is not None:
            try:
                grams = float(kwargs.get("grams", 0))
                price_value = float(price)
                content += (
                    f"\n\n按 {price_value:.2f} 元/克计算，"
                    f"{grams:.2f} 克黄金市值为 {grams * price_value:,.2f} 元。"
                )
            except (TypeError, ValueError):
                return SkillResult(False, "grams / price 必须为数字")
        return SkillResult(True, content)


__all__ = ["GoldAnalysisSkill"]
