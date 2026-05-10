from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class PlannerConfig:
    domain: str
    advisor_role: str
    default_target_role: str
    focus_keywords: list[str]
    avoid_directions: list[str]
    output_language: str
    job_data_dir: Path
    resume_dir: Path
    top_k: int
    market_top_k: int


def load_config() -> PlannerConfig:
    return PlannerConfig(
        domain=os.getenv("JMCP_DOMAIN", "AI 应用工程师"),
        advisor_role=os.getenv("JMCP_ADVISOR_ROLE", "职业规划顾问"),
        default_target_role=os.getenv(
            "JMCP_DEFAULT_TARGET_ROLE",
            "AI 应用工程师 / AI Agent 应用开发 / AI 自动化工程师",
        ),
        focus_keywords=_split_csv(
            os.getenv(
                "JMCP_FOCUS_KEYWORDS",
                "Python,RAG,Agent,FastAPI,Dify,n8n,Docker,RPA,API,LLM",
            )
        ),
        avoid_directions=_split_csv(
            os.getenv("JMCP_AVOID_DIRECTIONS", "纯算法岗,大模型预训练岗,底层推理优化岗")
        ),
        output_language=os.getenv("JMCP_OUTPUT_LANGUAGE", "zh-CN"),
        job_data_dir=Path(os.getenv("JMCP_JOB_DATA_DIR", "data/jobs")),
        resume_dir=Path(os.getenv("JMCP_RESUME_DIR", "data/resume")),
        top_k=int(os.getenv("JMCP_TOP_K", "8")),
        market_top_k=int(os.getenv("JMCP_MARKET_TOP_K", "50")),
    )
