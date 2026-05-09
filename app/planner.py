from __future__ import annotations

from dataclasses import dataclass

from app.config import PlannerConfig, load_config
from app.llm import invoke_llm
from app.loader import load_job_documents
from app.prompts import build_career_plan_prompt, build_system_prompt
from app.retriever import RetrievedJob, format_retrieved_jobs, retrieve_jobs


@dataclass(frozen=True)
class CareerPlanResult:
    plan: str
    target_role: str
    retrieval_query: str
    retrieved_jobs: list[RetrievedJob]
    retrieved_context: str
    system_prompt: str
    user_prompt: str
    document_count: int
    top_k: int


def build_retrieval_query(profile: str, target_role: str, config: PlannerConfig) -> str:
    focus_keywords = " ".join(config.focus_keywords)

    return f"目标职位:{target_role} 关键词:{focus_keywords} 个人背景:{profile}"


def generate_career_plan_result(profile: str, target_role: str | None = None) -> CareerPlanResult:
    config = load_config()
    resolved_target_role = target_role or config.default_target_role

    documents = load_job_documents(config.job_data_dir)

    if not documents:
        raise ValueError(f"No job markdown documents found in {config.job_data_dir}")

    retrieval_query = build_retrieval_query(profile, resolved_target_role, config)

    retrieved = retrieve_jobs(
        documents,
        retrieval_query,
        top_k=config.top_k,
        keywords=config.focus_keywords,
    )

    if not retrieved:
        raise ValueError("No relevant job documents retrieved.")

    retrieved_context = format_retrieved_jobs(retrieved)

    system_prompt = build_system_prompt(config)
    prompt = build_career_plan_prompt(profile, resolved_target_role, retrieved_context, config)

    plan = invoke_llm(system_prompt, prompt)

    return CareerPlanResult(
        plan=plan,
        target_role=resolved_target_role,
        retrieval_query=retrieval_query,
        retrieved_jobs=retrieved,
        retrieved_context=retrieved_context,
        system_prompt=system_prompt,
        user_prompt=prompt,
        document_count=len(documents),
        top_k=config.top_k,
    )


def generate_career_plan(profile: str, target_role: str | None = None) -> str:
    return generate_career_plan_result(profile, target_role=target_role).plan
