from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class JobDocument:
    id: str
    source_file: str
    title: str
    skills: list[str]
    content: str


def _extract_title(content: str) -> str:
    match = re.search(r"\*\*.*?岗位标题\*\*: ([^\n]+)", content)
    if match:
        return match.group(1).strip()
    fallback = re.search(r"^## 职位 \d+:?\s*(.*)$", content, flags=re.MULTILINE)
    if fallback and fallback.group(1).strip():
        return fallback.group(1).strip()
    return "Unknown title"


def _extract_skills(content: str) -> list[str]:
    match = re.search(r"\*\*技能点\*\*: ([^\n]+)", content)
    if not match:
        return []
    return [
        item.strip()
        for item in re.split(r"[,，、/|]", match.group(1))
        if item.strip()
    ]


def load_job_documents(data_dir: Path) -> list[JobDocument]:
    documents: list[JobDocument] = []

    for file_path in sorted(data_dir.glob("*.md")):
        if "岗位信息采集数据表" not in file_path.name:
            continue

        text = file_path.read_text(encoding="utf-8")
        chunks = re.split(r"(?=^## 职位 \d+:)", text, flags=re.MULTILINE)

        for index, chunk in enumerate(chunks, start=1):
            chunk = chunk.strip()

            if not chunk.startswith("## 职位"):
                continue

            doc_id = f"{file_path.stem}_{index}"
            documents.append(
                JobDocument(
                    id=doc_id,
                    source_file=file_path.name,
                    title=_extract_title(chunk),
                    skills=_extract_skills(chunk),
                    content=chunk,
                )
            )
            
    return documents
