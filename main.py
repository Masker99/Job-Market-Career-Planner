from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from app.config import load_config
from app.debug import render_retrieval_debug_report
from app.planner import generate_career_plan_result
from app.reporting import (
    add_sanitized_report_notice,
    build_sanitized_career_plan_report,
    build_timestamped_path,
    sanitize_report_text,
)
from app.resume_loader import read_resume_text


DEFAULT_REPORT_VERSION = "v5"
DEFAULT_OUTPUT_DIR = Path("outputs")
DEFAULT_REPORT_DIR = Path("reports")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _resolve_resume_path(raw_path: str) -> Path:
    config = load_config()
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return config.resume_dir / path


def _build_profile(profile: str | None, resume_file: str | None) -> str:
    parts: list[str] = []
    if resume_file and resume_file.strip():
        resume_path = _resolve_resume_path(resume_file.strip())
        parts.append(read_resume_text(resume_path))
    if profile and profile.strip():
        parts.append(profile.strip())
    if not parts:
        raise ValueError("请提供简历文件，或填写补充个人信息。")
    return "\n\n".join(parts)


def _ask_text(question: str, default: str | None = None) -> str:
    if default:
        answer = input(f"{question} [{default}]: ").strip()
        return answer or default
    return input(f"{question}: ").strip()


def _run_interactive(default_output: str | None) -> tuple[str, str, str | None]:
    config = load_config()

    print("Job Market Career Planner")
    print("直接回车可跳过可选项。\n")

    target_role = _ask_text("目标岗位/方向", config.default_target_role)
    resume_file = _ask_text(f"简历文件名或路径，默认从 {config.resume_dir} 读取，可跳过")
    profile = _ask_text("补充个人信息，可跳过")

    profile_text = _build_profile(profile, resume_file)
    return profile_text, target_role, default_output


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a career plan from job market data.")

    parser.add_argument(
        "--profile",
        default=None,
        help="User background text. Optional when --resume-file is provided.",
    )

    parser.add_argument(
        "--resume-file",
        default=None,
        help="Resume text/markdown/pdf file. Relative paths are resolved from JMCP_RESUME_DIR.",
    )

    parser.add_argument(
        "--target-role",
        default=None,
        help="Target role or career direction. Defaults to JMCP_DEFAULT_TARGET_ROLE.",
    )

    parser.add_argument(
        "--output",
        default=None,
        help="Path to save the full local career plan. Defaults to outputs/<version>_<timestamp>_career_plan.md.",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Write a Markdown report showing the retrieval query, matches, and prompt context.",
    )

    parser.add_argument(
        "--debug-output",
        default=None,
        help=(
            "Path to save the full local retrieval debug report when --debug is enabled. "
            "Defaults to outputs/<version>_<timestamp>_retrieval_debug.md."
        ),
    )

    parser.add_argument(
        "--report-version",
        default=DEFAULT_REPORT_VERSION,
        help="Version prefix used for default timestamped report filenames.",
    )

    parser.add_argument(
        "--report-dir",
        default=str(DEFAULT_REPORT_DIR),
        help="Directory for sanitized GitHub-friendly report copies.",
    )

    parser.add_argument(
        "--no-report-copy",
        action="store_true",
        help="Do not write sanitized copies to reports/.",
    )

    args = parser.parse_args()

    try:
        if not args.profile and not args.resume_file:
            profile, target_role, output = _run_interactive(args.output)
        else:
            profile = _build_profile(args.profile, args.resume_file)
            target_role = args.target_role
            output = args.output
    except (FileNotFoundError, ValueError) as exc:
        parser.error(str(exc))

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output or str(
        build_timestamped_path(
            DEFAULT_OUTPUT_DIR,
            "career_plan",
            version=args.report_version,
            timestamp=timestamp,
        )
    )
    debug_output = args.debug_output or str(
        build_timestamped_path(
            DEFAULT_OUTPUT_DIR,
            "retrieval_debug",
            version=args.report_version,
            timestamp=timestamp,
        )
    )
    report_dir = Path(args.report_dir)
    report_plan_path = build_timestamped_path(
        report_dir,
        "career_plan",
        version=args.report_version,
        timestamp=timestamp,
    )
    report_debug_path = build_timestamped_path(
        report_dir,
        "retrieval_debug",
        version=args.report_version,
        timestamp=timestamp,
    )

    print("正在检索岗位数据并生成职业规划，请稍等...", flush=True)

    try:
        result = generate_career_plan_result(profile, target_role=target_role)
    except KeyboardInterrupt:
        raise SystemExit("已取消生成。") from None
    except Exception as exc:
        raise SystemExit(f"生成失败：{exc}") from None

    output_path = Path(output)
    _write_text(output_path, result.plan)
    print(f"Saved career plan to {output_path}")

    if not args.no_report_copy:
        sanitized_plan = build_sanitized_career_plan_report(full_output_path=output_path)
        _write_text(report_plan_path, sanitized_plan)
        print(f"Saved sanitized career plan report to {report_plan_path}")

    if args.debug:
        debug_path = Path(debug_output)

        debug_report = render_retrieval_debug_report(
            target_role=result.target_role,
            retrieval_query=result.retrieval_query,
            retrieved_jobs=result.retrieved_jobs,
            retrieved_context=result.retrieved_context,
            market_profile_context=result.market_profile_context,
            market_job_count=len(result.market_jobs),
            system_prompt=result.system_prompt,
            user_prompt=result.user_prompt,
            document_count=result.document_count,
            top_k=result.top_k,
            query_expansion=result.query_expansion,
            retrieval_mode=result.retrieval_mode,
            vector_search_stats=result.vector_search_stats,
            market_top_k=result.market_top_k,
        )
        _write_text(debug_path, debug_report)
        print(f"Saved retrieval debug report to {debug_path}")

        if not args.no_report_copy:
            sanitized_debug_report = add_sanitized_report_notice(
                sanitize_report_text(debug_report, profile=profile)
            )
            _write_text(report_debug_path, sanitized_debug_report)
            print(f"Saved sanitized retrieval debug report to {report_debug_path}")


if __name__ == "__main__":
    main()
