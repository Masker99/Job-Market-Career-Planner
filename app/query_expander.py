from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any

from app.config import PlannerConfig
from app.llm import invoke_llm
from app.prompts import build_query_expansion_prompt


@dataclass(frozen=True)
class QueryExpansion:
    mode: str
    original_target_role: str
    expanded_roles: list[str]
    related_skills: list[str]
    related_tools: list[str]
    excluded_terms: list[str]
    final_query_terms: list[str]
    source: str


def _is_mock_enabled() -> bool:
    return os.getenv("JMCP_MOCK", "0").strip().lower() in {"1", "true", "yes", "on"}


def _dedupe(items: list[str], *, limit: int) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        normalized = re.sub(r"\s+", " ", str(item)).strip()
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(normalized)
        if len(result) >= limit:
            break
    return result


def _empty_expansion(target_role: str, *, mode: str = "off") -> QueryExpansion:
    return QueryExpansion(
        mode=mode,
        original_target_role=target_role,
        expanded_roles=[],
        related_skills=[],
        related_tools=[],
        excluded_terms=[],
        final_query_terms=[],
        source="disabled",
    )


def _fallback_expansion(target_role: str, config: PlannerConfig, *, source: str) -> QueryExpansion:
    base_terms = [target_role, *config.focus_keywords]
    expanded_roles: list[str] = []
    related_skills: list[str] = []
    related_tools: list[str] = []

    target_lower = target_role.lower()
    if "agent" in target_lower or "智能体" in target_role:
        expanded_roles.extend(
            [
                "AI 应用工程师",
                "LLM 应用开发",
                "大模型应用开发",
                "智能体开发",
                "RAG 应用开发",
                "AI 自动化工程师",
            ]
        )
        related_skills.extend(["RAG", "Agent", "LLM", "知识库", "向量数据库", "API 集成"])
        related_tools.extend(["LangChain", "LangGraph", "Dify", "Coze", "n8n", "FastAPI"])

    final_terms = _dedupe(
        [*expanded_roles, *related_skills, *related_tools, *base_terms],
        limit=config.query_expansion_max_terms,
    )

    return QueryExpansion(
        mode=config.query_expansion_mode,
        original_target_role=target_role,
        expanded_roles=_dedupe(expanded_roles, limit=12),
        related_skills=_dedupe(related_skills, limit=12),
        related_tools=_dedupe(related_tools, limit=12),
        excluded_terms=config.avoid_directions,
        final_query_terms=final_terms,
        source=source,
    )


def _extract_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?", "", stripped, flags=re.IGNORECASE).strip()
        stripped = re.sub(r"```$", "", stripped).strip()

    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", stripped, flags=re.DOTALL)
        if not match:
            raise
        parsed = json.loads(match.group(0))

    if not isinstance(parsed, dict):
        raise ValueError("Query expansion response must be a JSON object.")
    return parsed


def _list_from_json(data: dict[str, Any], key: str) -> list[str]:
    value = data.get(key, [])
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def expand_retrieval_query(profile: str, target_role: str, config: PlannerConfig) -> QueryExpansion:
    mode = config.query_expansion_mode.strip().lower()
    if mode in {"", "off", "none", "false", "0"}:
        return _empty_expansion(target_role)

    if mode != "llm":
        return _fallback_expansion(target_role, config, source="fallback-unsupported-mode")

    if _is_mock_enabled():
        return _fallback_expansion(target_role, config, source="fallback-mock")

    system_prompt, user_prompt = build_query_expansion_prompt(profile, target_role, config)
    try:
        content = invoke_llm(system_prompt, user_prompt)
        data = _extract_json_object(content)
    except Exception:
        return _fallback_expansion(target_role, config, source="fallback-llm-error")

    expanded_roles = _dedupe(_list_from_json(data, "expanded_roles"), limit=12)
    related_skills = _dedupe(_list_from_json(data, "related_skills"), limit=12)
    related_tools = _dedupe(_list_from_json(data, "related_tools"), limit=12)
    excluded_terms = _dedupe(
        [*_list_from_json(data, "excluded_terms"), *config.avoid_directions],
        limit=12,
    )
    final_query_terms = _dedupe(
        [
            *_list_from_json(data, "final_query_terms"),
            *expanded_roles,
            *related_skills,
            *related_tools,
            target_role,
            *config.focus_keywords,
        ],
        limit=config.query_expansion_max_terms,
    )

    return QueryExpansion(
        mode=mode,
        original_target_role=target_role,
        expanded_roles=expanded_roles,
        related_skills=related_skills,
        related_tools=related_tools,
        excluded_terms=excluded_terms,
        final_query_terms=final_query_terms,
        source="llm",
    )
