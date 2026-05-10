from __future__ import annotations

import re
from pathlib import Path


PROFILE_REDACTION = "[REDACTED_USER_PROFILE]"
PROMPT_REDACTION = "[REDACTED_FINAL_USER_PROMPT]"


def build_timestamped_path(directory: Path, kind: str, *, version: str, timestamp: str) -> Path:
    return directory / f"{version}_{timestamp}_{kind}.md"


def _redact_known_profile(text: str, profile: str) -> str:
    profile = profile.strip()
    if not profile:
        return text
    return text.replace(profile, PROFILE_REDACTION)


def _redact_personal_background_fields(text: str) -> str:
    patterns = [
        r"(个人背景[:：]).*?(?=\n```|\n\n|$)",
        r"(用户背景[:：]).*?(?=\n```|\n\n|$)",
    ]
    redacted = text
    for pattern in patterns:
        redacted = re.sub(
            pattern,
            rf"\1 {PROFILE_REDACTION}",
            redacted,
            flags=re.DOTALL,
        )
    return redacted


def _redact_final_user_prompt_preview(text: str) -> str:
    return re.sub(
        r"## Final User Prompt Preview\n\n```markdown\n.*?\n```",
        f"## Final User Prompt Preview\n\n```markdown\n{PROMPT_REDACTION}\n```",
        text,
        flags=re.DOTALL,
    )


def sanitize_report_text(text: str, *, profile: str) -> str:
    redacted = _redact_known_profile(text, profile)
    redacted = _redact_personal_background_fields(redacted)
    redacted = _redact_final_user_prompt_preview(redacted)
    return redacted


def add_sanitized_report_notice(text: str) -> str:
    notice = (
        "> This report is a sanitized GitHub-friendly copy. "
        "Personal resume/background details and final user prompt content are redacted.\n\n"
    )
    return notice + text


def build_sanitized_career_plan_report(*, full_output_path: Path) -> str:
    return "\n".join(
        [
            "> This report is a sanitized GitHub-friendly copy.",
            "> The generated career plan can infer or restate private resume/background details,",
            "> so the GitHub copy intentionally omits the full generated plan.",
            "",
            "# Sanitized Career Plan Report",
            "",
            "The full local career plan was generated successfully and saved under `outputs/`.",
            "",
            f"- Local full output: `{full_output_path}`",
            "- GitHub copy: generated plan body redacted",
            "",
            "Use the paired sanitized retrieval debug report to review the RAG evidence,",
            "query expansion, market profile, and representative job matches without exposing",
            "private resume/background content.",
            "",
        ]
    )
