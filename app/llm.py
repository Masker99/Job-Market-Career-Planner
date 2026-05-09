from __future__ import annotations

import os
from typing import Any, cast

from dotenv import load_dotenv

load_dotenv()

_llm: Any | None = None


def _is_mock_enabled() -> bool:
    return os.getenv("JMCP_MOCK", "0").strip().lower() in {"1", "true", "yes", "on"}


def build_llm() -> Any:
    from langchain_deepseek import ChatDeepSeek
    from pydantic import SecretStr

    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY environment variable is not set.")

    return ChatDeepSeek(
        model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        api_key=SecretStr(api_key),
        temperature=float(os.getenv("DEEPSEEK_TEMPERATURE", "0.3")),
        timeout=float(os.getenv("DEEPSEEK_TIMEOUT", "60")),
        max_retries=int(os.getenv("DEEPSEEK_MAX_RETRIES", "2")),
    )


def invoke_llm(system_prompt: str, user_prompt: str) -> str:
    if _is_mock_enabled():
        return (
            "# Mock Career Plan\n\n"
            "这是 mock 模式输出，用于验证 RAG 链路是否跑通。\n\n"
            "## 检索证据摘要\n\n"
            f"{user_prompt[:1200]}...\n\n"
            "## 下一步\n\n"
            "将 `JMCP_MOCK=0` 并配置真实 `DEEPSEEK_API_KEY` 后，可以生成完整转型计划。\n"
        )

    global _llm
    if _llm is None:
        _llm = build_llm()

    from langchain_core.messages import HumanMessage, SystemMessage

    response = cast(Any, _llm).invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
    )

    content = str(response.content).strip()

    if not content:
        raise ValueError("LLM returned empty content.")

    return content
