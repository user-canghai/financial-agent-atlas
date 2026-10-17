from __future__ import annotations

from Financial_Agent.skills.base_skill import BaseSkill, SkillResult


class CompanyQuerySkill(BaseSkill):
    name = "company"
    description = "查询公司档案与财务概况（Mock 数据）"
    keywords = ("公司", "上市公司", "财务", "profile", "company")

    def execute(self, **kwargs) -> SkillResult:
        from Financial_Agent.tools.tools import database_search, get_company_profile

        company_name = str(kwargs.get("company_name", "")).strip()
        profile = get_company_profile.invoke({"company_name": company_name})
        finance = database_search.invoke({"query": company_name})
        return SkillResult(True, f"{profile}\n\n{finance}")


__all__ = ["CompanyQuerySkill"]
