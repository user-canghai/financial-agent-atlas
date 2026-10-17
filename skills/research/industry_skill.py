from __future__ import annotations

from Financial_Agent.skills.base_skill import BaseSkill, SkillResult


class IndustryResearchSkill(BaseSkill):
    name = "industry-research"
    description = "生成行业研究报告框架与图片规划"
    keywords = ("行业", "研究", "报告", "industry", "research")

    def execute(self, **kwargs) -> SkillResult:
        topic = str(kwargs.get("topic", "目标行业"))
        content = f"""# {topic}研究报告框架

1. 行业概述
   - 定义、边界与产业链
   - 市场规模与增速

2. 核心驱动因素
   - 技术、政策、需求、资本

3. 竞争格局
   - 主要参与者
   - 商业模式与壁垒

4. 应用场景与案例

5. 趋势与展望
   - 短期（1 年）
   - 中期（3 年）

**图片规划**
- `{topic}_overview.png`：行业概览（放在引言之后）
- `{topic}_value_chain.png`：产业链示意（放在行业概述之后）
- `{topic}_trend.png`：趋势图（放在展望章节）"""
        return SkillResult(True, content)


__all__ = ["IndustryResearchSkill"]
