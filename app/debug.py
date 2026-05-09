from __future__ import annotations

from app.retriever import RetrievedJob


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "\n\n...[truncated]"


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
) -> str:
    sections: list[str] = [
        "# RAG Retrieval Debug Report",
        "",
        "## Run Summary",
        "",
        f"- Target role: {target_role}",
        f"- Loaded job documents: {document_count}",
        f"- Requested top_k: {top_k}",
        f"- Retrieved jobs: {len(retrieved_jobs)}",
        "",
        "## Retrieval Query",
        "",
        "```text",
        retrieval_query,
        "```",
        "",
        "## Retrieved Jobs",
        "",
    ]

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
