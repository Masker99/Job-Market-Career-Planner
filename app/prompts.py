from __future__ import annotations

from app.config import PlannerConfig


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
) -> str:
    focus_keywords = "、".join(config.focus_keywords)
    return f"""
请基于用户背景、目标方向和检索到的岗位市场数据，生成一份定制化转型计划。

用户背景：
{profile}

目标方向：
{target_role}

重点关注技能/关键词：
{focus_keywords}

检索到的岗位市场证据：
{retrieved_jobs}

请按以下结构输出 Markdown：

## 1. 推荐定位
- 推荐 1-2 个最适合的岗位方向。
- 说明为什么这些方向和用户背景匹配。

## 2. 市场要求摘要
- 总结检索岗位中反复出现的技能要求。
- 必须引用岗位证据中的岗位标题、技能点或正文关键词。

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
