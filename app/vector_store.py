from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from app.config import PlannerConfig
from app.embeddings import cosine_similarity, embed_text
from app.loader import JobDocument
from app.retriever import RetrievedJob


@dataclass(frozen=True)
class VectorSearchStats:
    provider: str
    index_path: Path
    indexed_documents: int
    query_dimension: int
    top_similarity: float


def build_document_embedding_text(document: JobDocument) -> str:
    skills = ", ".join(document.skills)
    return "\n".join(
        [
            f"Title: {document.title}",
            f"Skills: {skills}",
            document.content,
        ]
    )


def _overlapping_terms(document: JobDocument, terms: list[str]) -> list[str]:
    haystack = " ".join([document.title, " ".join(document.skills), document.content]).lower()
    matched: list[str] = []
    for term in terms:
        normalized = term.strip()
        if normalized and normalized.lower() in haystack:
            matched.append(normalized)

    return matched


def build_vector_index(documents: list[JobDocument], config: PlannerConfig) -> None:
    index_path = config.vector_index_path
    index_path.parent.mkdir(parents=True, exist_ok=True)

    with index_path.open("w", encoding="utf-8") as file:
        for document in documents:
            embedding_text = build_document_embedding_text(document)
            record = {
                "id": document.id,
                "source_file": document.source_file,
                "title": document.title,
                "skills": document.skills,
                "content": document.content,
                "embedding": embed_text(embedding_text, dimension=config.embedding_dimension),
            }
            file.write(json.dumps(record, ensure_ascii=False) + "\n")


def _load_index(index_path: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    if not index_path.exists():
        return records

    with index_path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    return records


def _needs_rebuild(index_path: Path, documents: list[JobDocument]) -> bool:
    records = _load_index(index_path)
    if len(records) != len(documents):
        return True
    indexed_ids = {str(record.get("id", "")) for record in records}
    document_ids = {document.id for document in documents}

    return indexed_ids != document_ids


def ensure_vector_index(documents: list[JobDocument], config: PlannerConfig) -> None:
    if _needs_rebuild(config.vector_index_path, documents):
        build_vector_index(documents, config)


def search_vector_index(
    documents: list[JobDocument],
    query: str,
    *,
    top_k: int,
    config: PlannerConfig,
    query_terms: list[str],
) -> tuple[list[RetrievedJob], VectorSearchStats]:
    ensure_vector_index(documents, config)
    records = _load_index(config.vector_index_path)
    documents_by_id = {document.id: document for document in documents}
    query_embedding = embed_text(query, dimension=config.embedding_dimension)

    scored: list[tuple[float, RetrievedJob]] = []
    for record in records:
        document_id = str(record.get("id", ""))
        document = documents_by_id.get(document_id)
        embedding = record.get("embedding")
        if document is None or not isinstance(embedding, list):
            continue

        similarity = cosine_similarity(
            query_embedding,
            [float(value) for value in embedding],
        )
        score = int(round(similarity * 10000))
        matched_terms = _overlapping_terms(document, query_terms)
        scored.append(
            (
                similarity,
                RetrievedJob(
                    document=document,
                    score=score,
                    matched_terms=matched_terms,
                ),
            )
        )

    scored.sort(key=lambda item: item[0], reverse=True)
    results = [item for _, item in scored[:top_k]]
    top_similarity = scored[0][0] if scored else 0.0
    stats = VectorSearchStats(
        provider=config.embedding_provider,
        index_path=config.vector_index_path,
        indexed_documents=len(records),
        query_dimension=len(query_embedding),
        top_similarity=top_similarity,
    )
    return results, stats
