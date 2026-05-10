from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

from app.retriever import RetrievedJob


@dataclass(frozen=True)
class FrequencyItem:
    value: str
    count: int


@dataclass(frozen=True)
class MarketProfile:
    candidate_count: int
    top_skills: list[FrequencyItem]
    top_titles: list[FrequencyItem]
    top_matched_terms: list[FrequencyItem]
    experience_distribution: list[FrequencyItem]
    education_distribution: list[FrequencyItem]
    salary_distribution: list[FrequencyItem]


def _top_items(counter: Counter[str], limit: int) -> list[FrequencyItem]:
    return [
        FrequencyItem(value=value, count=count)
        for value, count in counter.most_common(limit)
        if value
    ]


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _extract_markdown_field(content: str, label: str) -> str | None:
    pattern = rf"\*\*[^*\n]*{re.escape(label)}[^*\n]*\*\*:\s*([^\n]+)"
    match = re.search(pattern, content)
    if not match:
        return None

    value = _normalize(match.group(1))
    if not value or value.upper() in {"N/A", "NA", "NONE", "UNKNOWN"}:
        return None
    return value


def build_market_profile(items: list[RetrievedJob], *, top_n: int = 15) -> MarketProfile:
    skill_counts: Counter[str] = Counter()
    title_counts: Counter[str] = Counter()
    matched_term_counts: Counter[str] = Counter()
    experience_counts: Counter[str] = Counter()
    education_counts: Counter[str] = Counter()
    salary_counts: Counter[str] = Counter()

    for item in items:
        document = item.document
        if document.title and document.title != "Unknown title":
            title_counts[_normalize(document.title)] += 1

        for skill in document.skills:
            normalized_skill = _normalize(skill)
            if normalized_skill:
                skill_counts[normalized_skill] += 1

        for term in item.matched_terms:
            normalized_term = _normalize(term)
            if normalized_term:
                matched_term_counts[normalized_term] += 1

        experience = _extract_markdown_field(document.content, "经验")
        if experience:
            experience_counts[experience] += 1

        education = _extract_markdown_field(document.content, "学历")
        if education:
            education_counts[education] += 1

        salary = _extract_markdown_field(document.content, "薪资")
        if salary:
            salary_counts[salary] += 1

    return MarketProfile(
        candidate_count=len(items),
        top_skills=_top_items(skill_counts, top_n),
        top_titles=_top_items(title_counts, top_n),
        top_matched_terms=_top_items(matched_term_counts, top_n),
        experience_distribution=_top_items(experience_counts, top_n),
        education_distribution=_top_items(education_counts, top_n),
        salary_distribution=_top_items(salary_counts, top_n),
    )


def _format_frequency_section(title: str, items: list[FrequencyItem]) -> str:
    lines = [f"## {title}"]
    if not items:
        lines.append("- No structured data found.")
        return "\n".join(lines)

    for item in items:
        lines.append(f"- {item.value}: {item.count}")
    return "\n".join(lines)


def format_market_profile(profile: MarketProfile) -> str:
    sections = [
        "# Market Profile",
        "",
        f"Candidate job count: {profile.candidate_count}",
        "",
        _format_frequency_section("High-Frequency Skills", profile.top_skills),
        "",
        _format_frequency_section("High-Frequency Job Titles", profile.top_titles),
        "",
        _format_frequency_section("High-Frequency Matched Terms", profile.top_matched_terms),
        "",
        _format_frequency_section("Experience Distribution", profile.experience_distribution),
        "",
        _format_frequency_section("Education Distribution", profile.education_distribution),
        "",
        _format_frequency_section("Salary Distribution", profile.salary_distribution),
    ]
    return "\n".join(sections)
