from __future__ import annotations

import re
from dataclasses import dataclass

from app.loader import JobDocument


DEFAULT_KEYWORDS = [
    "Python",
    "FastAPI",
    "Flask",
    "RAG",
    "Agent",
    "LangChain",
    "LangGraph",
    "Dify",
    "Coze",
    "n8n",
    "OpenClaw",
    "MCP",
    "Function Calling",
    "Prompt",
    "LLM",
    "大模型",
    "知识库",
    "向量数据库",
    "Docker",
    "Linux",
    "Git",
    "API",
    "数据库",
    "MySQL",
    "PostgreSQL",
    "RPA",
    "自动化",
    "飞书",
    "客服",
    "电商",
    "跨境",
]


@dataclass(frozen=True)
class RetrievedJob:
    document: JobDocument
    score: int
    matched_terms: list[str]


def _contains(text: str, term: str) -> bool:
    return re.search(re.escape(term), text, flags=re.IGNORECASE) is not None


def retrieve_jobs(
    documents: list[JobDocument],
    query: str,
    *,
    top_k: int,
    keywords: list[str] | None = None,
) -> list[RetrievedJob]:
    terms = keywords or DEFAULT_KEYWORDS
    scored: list[RetrievedJob] = []

    for document in documents:
        matched_terms: list[str] = []
        score = 0
        skill_text = " ".join(document.skills)
        for term in terms:
            query_has_term = _contains(query, term)
            title_has_term = _contains(document.title, term)
            skill_has_term = _contains(skill_text, term)
            content_has_term = _contains(document.content, term)

            if query_has_term and title_has_term:
                matched_terms.append(term)
                score += 6
            elif query_has_term and skill_has_term:
                matched_terms.append(term)
                score += 5
            elif query_has_term and content_has_term:
                matched_terms.append(term)
                score += 3

            if title_has_term:
                score += 2
            if skill_has_term:
                score += 2
            elif content_has_term:
                score += 1

        if score > 0:
            scored.append(RetrievedJob(document=document, score=score, matched_terms=matched_terms))

    scored.sort(key=lambda item: item.score, reverse=True)
    return scored[:top_k]


def format_retrieved_jobs(items: list[RetrievedJob], *, max_chars_per_job: int = 1600) -> str:
    sections: list[str] = []
    for index, item in enumerate(items, start=1):
        content = item.document.content[:max_chars_per_job]
        sections.append(
            "\n".join(
                [
                    f"### 检索结果 {index}",
                    f"- 来源文件：{item.document.source_file}",
                    f"- 岗位标题：{item.document.title}",
                    f"- 技能点：{', '.join(item.document.skills) if item.document.skills else '未显式标注'}",
                    f"- 匹配分数：{item.score}",
                    f"- 命中关键词：{', '.join(sorted(set(item.matched_terms)))}",
                    "",
                    content,
                ]
            )
        )
    return "\n\n---\n\n".join(sections)
