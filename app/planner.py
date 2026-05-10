from __future__ import annotations

from dataclasses import dataclass

from app.config import PlannerConfig, load_config
from app.llm import invoke_llm
from app.loader import load_job_documents
from app.market_profile import MarketProfile, build_market_profile, format_market_profile
from app.prompts import build_career_plan_prompt, build_system_prompt
from app.query_expander import QueryExpansion, expand_retrieval_query
from app.retriever import RetrievedJob, format_retrieved_jobs, retrieve_jobs


@dataclass(frozen=True)
class CareerPlanResult:
    plan: str
    target_role: str
    retrieval_query: str
    query_expansion: QueryExpansion
    retrieved_jobs: list[RetrievedJob]
    retrieved_context: str
    market_jobs: list[RetrievedJob]
    market_profile: MarketProfile
    market_profile_context: str
    system_prompt: str
    user_prompt: str
    document_count: int
    top_k: int
    market_top_k: int


def build_retrieval_query(
    profile: str,
    target_role: str,
    config: PlannerConfig,
    query_expansion: QueryExpansion | None = None,
) -> str:
    focus_keywords = " ".join(config.focus_keywords)
    expansion_terms = ""
    if query_expansion and query_expansion.final_query_terms:
        expansion_terms = f" 扩展检索词:{' '.join(query_expansion.final_query_terms)}"

    return f"目标职位:{target_role}{expansion_terms} 关键词:{focus_keywords} 个人背景:{profile}"


def _build_retrieval_keywords(config: PlannerConfig, query_expansion: QueryExpansion) -> list[str]:
    return list(dict.fromkeys([*config.focus_keywords, *query_expansion.final_query_terms]))


def generate_career_plan_result(profile: str, target_role: str | None = None) -> CareerPlanResult:
    config = load_config()
    resolved_target_role = target_role or config.default_target_role

    documents = load_job_documents(config.job_data_dir)

    if not documents:
        raise ValueError(f"No job markdown documents found in {config.job_data_dir}")

    query_expansion = expand_retrieval_query(profile, resolved_target_role, config)
    retrieval_query = build_retrieval_query(profile, resolved_target_role, config, query_expansion)
    retrieval_keywords = _build_retrieval_keywords(config, query_expansion)

    market_retrieved = retrieve_jobs(
        documents,
        retrieval_query,
        top_k=max(config.market_top_k, config.top_k),
        keywords=retrieval_keywords,
    )

    if not market_retrieved:
        raise ValueError("No relevant job documents retrieved.")

    retrieved = market_retrieved[: config.top_k]
    market_profile = build_market_profile(market_retrieved)
    market_profile_context = format_market_profile(market_profile)
    retrieved_context = format_retrieved_jobs(retrieved)

    system_prompt = build_system_prompt(config)
    prompt = build_career_plan_prompt(
        profile,
        resolved_target_role,
        retrieved_context,
        config,
        market_profile=market_profile_context,
    )

    plan = invoke_llm(system_prompt, prompt)

    return CareerPlanResult(
        plan=plan,
        target_role=resolved_target_role,
        retrieval_query=retrieval_query,
        query_expansion=query_expansion,
        retrieved_jobs=retrieved,
        retrieved_context=retrieved_context,
        market_jobs=market_retrieved,
        market_profile=market_profile,
        market_profile_context=market_profile_context,
        system_prompt=system_prompt,
        user_prompt=prompt,
        document_count=len(documents),
        top_k=config.top_k,
        market_top_k=max(config.market_top_k, config.top_k),
    )


def generate_career_plan(profile: str, target_role: str | None = None) -> str:
    return generate_career_plan_result(profile, target_role=target_role).plan
