from __future__ import annotations

from Financial_Agent.skills.base_skill import BaseSkill, SkillResult


class MacroAnalysisSkill(BaseSkill):
    name = "macro"
    description = "生成宏观经济分析框架，覆盖增长、物价、就业、政策与风险"
    keywords = ("宏观", "经济", "GDP", "通胀", "政策")

    def execute(self, **kwargs) -> SkillResult:
        topic = str(kwargs.get("topic", "宏观经济形势"))
        period = str(kwargs.get("period", "最新年度"))
        content = f"""# {period}{topic}分析框架

**一、总体运行**
- GDP 增速、总量与结构变化
- 三次产业贡献

**二、需求侧**
- 消费、投资、净出口
- 内需恢复情况

**三、物价与就业**
- CPI / PPI 走势
- 就业与居民收入

**四、政策环境**
- 财政政策
- 货币政策
- 产业政策

**五、风险与展望**
- 外部环境
- 内部结构性压力
- 下一阶段判断

> 说明：以上为分析框架。正式报告中的统计数据需通过数据库或联网搜索核实，
> 并注明来源与统计口径。"""
        return SkillResult(True, content)


__all__ = ["MacroAnalysisSkill"]
