from __future__ import annotations

from app.query_expander import QueryExpansion
from app.retriever import RetrievedJob


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "\n\n...[truncated]"


def _format_list(items: list[str]) -> list[str]:
    if not items:
        return ["- None"]
    return [f"- {item}" for item in items]


def render_retrieval_debug_report(
    *,
    target_role: str,
    retrieval_query: str,
    retrieved_jobs: list[RetrievedJob],
    retrieved_context: str,
    system_prompt: str,
    user_prompt: str,
    document_count: int,
    top_k: int,
    query_expansion: QueryExpansion | None = None,
    market_profile_context: str | None = None,
    market_job_count: int | None = None,
    market_top_k: int | None = None,
) -> str:
    market_top_k_value = market_top_k if market_top_k is not None else top_k
    market_job_count_value = market_job_count if market_job_count is not None else len(retrieved_jobs)
    sections: list[str] = [
        "# RAG Retrieval Debug Report",
        "",
        "## Run Summary",
        "",
        f"- Target role: {target_role}",
        f"- Loaded job documents: {document_count}",
        f"- Requested market_top_k: {market_top_k_value}",
        f"- Market profile candidate jobs: {market_job_count_value}",
        f"- Representative top_k: {top_k}",
        f"- Representative jobs: {len(retrieved_jobs)}",
        "",
        "## Retrieval Query",
        "",
        "```text",
        retrieval_query,
        "```",
        "",
    ]

    if query_expansion:
        sections.extend(
            [
                "## Query Expansion",
                "",
                f"- Mode: {query_expansion.mode}",
                f"- Source: {query_expansion.source}",
                f"- Original target role: {query_expansion.original_target_role}",
                "",
                "### Expanded Roles",
                *_format_list(query_expansion.expanded_roles),
                "",
                "### Related Skills",
                *_format_list(query_expansion.related_skills),
                "",
                "### Related Tools",
                *_format_list(query_expansion.related_tools),
                "",
                "### Excluded Terms",
                *_format_list(query_expansion.excluded_terms),
                "",
                "### Final Query Terms",
                *_format_list(query_expansion.final_query_terms),
                "",
            ]
        )

    if market_profile_context:
        sections.extend(
            [
                "## Market Profile",
                "",
                "```markdown",
                _truncate(market_profile_context, 4000),
                "```",
                "",
            ]
        )

    sections.extend(["## Representative Jobs", ""])

    for index, item in enumerate(retrieved_jobs, start=1):
        matched_terms = ", ".join(sorted(set(item.matched_terms))) or "None"
        skills = ", ".join(item.document.skills) or "None"
        preview = _truncate(item.document.content, 700)
        sections.extend(
            [
                f"### {index}. {item.document.title}",
                "",
                f"- Document ID: `{item.document.id}`",
                f"- Source file: `{item.document.source_file}`",
                f"- Score: {item.score}",
                f"- Matched terms: {matched_terms}",
                f"- Skills: {skills}",
                "",
                "```text",
                preview,
                "```",
                "",
            ]
        )

    sections.extend(
        [
            "## Prompt Context Preview",
            "",
            "```markdown",
            _truncate(retrieved_context, 3000),
            "```",
            "",
            "## System Prompt",
            "",
            "```text",
            _truncate(system_prompt, 2000),
            "```",
            "",
            "## Final User Prompt Preview",
            "",
            "```markdown",
            _truncate(user_prompt, 4000),
            "```",
            "",
        ]
    )

    return "\n".join(sections)
