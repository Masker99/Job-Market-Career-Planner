from __future__ import annotations

from app.config import PlannerConfig


def build_query_expansion_prompt(
    profile: str,
    target_role: str,
    config: PlannerConfig,
) -> tuple[str, str]:
    system_prompt = """
你是 RAG 系统中的检索查询改写器，负责把用户的目标岗位改写成更适合检索招聘岗位数据的表达。
你只能返回严格 JSON，不要输出 Markdown、解释、职业建议或学习计划。
扩展词必须贴近目标岗位，并且要有助于检索招聘 JD。
除非目标岗位明确需要，否则不要扩展到排除方向或明显不同的职业方向。
""".strip()

    user_prompt = f"""
原始目标岗位：
{target_role}

用户背景：
{profile[:1200]}

当前重点关键词：
{", ".join(config.focus_keywords)}

默认不优先方向：
{", ".join(config.avoid_directions) if config.avoid_directions else "None"}

请只生成包含以下字段的 JSON：
{{
  "expanded_roles": ["与目标岗位相近的岗位名称或市场常见表达"],
  "related_skills": ["有助于检索相关岗位的技能词"],
  "related_tools": ["有助于检索相关岗位的工具、框架或平台"],
  "excluded_terms": ["不应该优先检索的方向或词"],
  "final_query_terms": ["去重后的最终检索词"]
}}

规则：
- 每个列表都要简洁，不要堆砌无关词。
- expanded_roles 应该优先使用中文招聘市场中常见的岗位表达。
- related_skills 和 related_tools 应该服务于岗位检索，不要写学习建议。
- 不要扩展到明显不同的职业路径。
- 除非目标岗位明确要求，否则不要包含模型预训练、算法研究、底层推理优化等方向。
- final_query_terms 最多 {config.query_expansion_max_terms} 个。
""".strip()

    return system_prompt, user_prompt


def build_system_prompt(config: PlannerConfig) -> str:
    avoid = "、".join(config.avoid_directions) if config.avoid_directions else "无"
    return f"""
你是{config.advisor_role}，擅长基于真实招聘岗位数据，为候选人制定务实、可执行的职业转型计划。

当前规划领域：
{config.domain}

输出语言：
{config.output_language}

你必须：
- 把建议和岗位证据关联起来。
- 不输出空泛鸡汤。
- 不夸大转型难度或收益。
- 区分“已有能力”“能力差距”“短期补齐优先级”。
- 除非岗位证据明确支持，否则不要优先推荐这些方向：{avoid}。
""".strip()


def build_career_plan_prompt(
    profile: str,
    target_role: str,
    retrieved_jobs: str,
    config: PlannerConfig,
    market_profile: str | None = None,
) -> str:
    focus_keywords = "、".join(config.focus_keywords)
    market_profile_section = ""
    if market_profile:
        market_profile_section = f"""

岗位市场画像（基于更多候选岗位的结构化统计）：
{market_profile}
"""

    return f"""
请基于用户背景、目标方向和检索到的岗位市场数据，生成一份定制化转型计划。

用户背景：
{profile}

目标方向：
{target_role}

重点关注技能/关键词：
{focus_keywords}
{market_profile_section}

检索到的岗位市场证据：
{retrieved_jobs}

请按以下结构输出 Markdown：

## 1. 推荐定位
- 推荐 1-2 个最适合的岗位方向。
- 说明为什么这些方向和用户背景匹配。

## 2. 市场要求摘要
- 优先基于“岗位市场画像”总结高频技能、高频职责、经验、学历和薪资分布。
- 再用代表性岗位证据支撑市场共性结论。
- 必须区分“市场共性要求”和“单个岗位特殊要求”。

## 3. 用户优势
- 说明用户已有经验如何迁移到目标岗位。

## 4. 技能差距
- 列出必须补齐、优先补齐、暂时不急的能力。

## 5. 30 天学习计划
- 按周拆解。
- 每周必须有可交付成果。

## 6. 作品集项目建议
- 给出 1 个主项目和 1 个辅助项目。
- 说明项目为什么匹配岗位要求。

## 7. 简历关键词
- 给出可以放进简历的技能词和项目表达。

## 8. 投递策略
- 推荐投递哪些岗位标题。
- 哪些岗位暂时不建议主攻。

要求：
- 必须基于岗位数据，不要泛泛而谈。
- 不要偏离目标方向，除非岗位证据明显说明目标方向不适合。
- 输出要具体、克制、可执行。
- 如果岗位证据不足，要明确说明。
""".strip()
