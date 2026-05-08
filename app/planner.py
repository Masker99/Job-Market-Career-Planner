from __future__ import annotations

from app.config import PlannerConfig, load_config
from app.llm import invoke_llm
from app.loader import load_job_documents
from app.prompts import build_career_plan_prompt, build_system_prompt
from app.retriever import format_retrieved_jobs, retrieve_jobs


def build_retrieval_query(profile: str, target_role: str, config: PlannerConfig) -> str:
    focus_keywords = " ".join(config.focus_keywords)
    return f"{target_role} {focus_keywords} {profile}"


def generate_career_plan(profile: str, target_role: str | None = None) -> str:
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
    prompt = build_career_plan_prompt(profile, resolved_target_role, retrieved_context, config)
    
    return invoke_llm(build_system_prompt(config), prompt)
