"""Evaluate existing unevaluated jobs and refresh the Excel tracker."""

import argparse
import os
import sqlite3

from ai_evaluator import EvaluationError, evaluate_job, extract_resume_text
from database import DATABASE_PATH, save_ai_evaluation
from excel_tracker import EXCEL_PATH, sync_excel
from local_ai import (
    LOCAL_AI_THRESHOLD,
    LocalAIError,
    evaluate_local_job,
)


def _load_jobs(query, parameters=()):
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    try:
        return [dict(row) for row in connection.execute(query, parameters)]
    finally:
        connection.close()


def _save_local_evaluation(url, result):
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        connection.execute(
            """UPDATE jobs
               SET local_ai_relevant = ?, local_ai_score = ?, local_ai_reason = ?,
                   local_ai_evaluated_at = datetime('now')
               WHERE url = ? AND local_ai_evaluated_at IS NULL""",
            (int(result["relevant"]), result["score"], result["reason"], url),
        )
        connection.commit()
    finally:
        connection.close()


def _apply_limit(jobs, limit):
    return jobs if limit is None else jobs[:limit]


def _backfill_local(limit):
    jobs = _load_jobs(
        """SELECT company, title, description, location, url, source, posted_at
           FROM jobs WHERE local_ai_evaluated_at IS NULL ORDER BY id"""
    )
    jobs = _apply_limit(jobs, limit)
    print(f"Running local AI for {len(jobs)} unevaluated jobs.")
    succeeded = 0
    for job in jobs:
        try:
            result = evaluate_local_job(job)
            _save_local_evaluation(job["url"], result)
        except (LocalAIError, sqlite3.Error) as error:
            print(f"LOCAL AI FAILED: {job['title']}: {error}")
            continue
        succeeded += 1
        print(f"LOCAL AI: {result['score']} - {job['title']}")
    print(f"Local AI complete: {succeeded}/{len(jobs)} evaluated.")


def _backfill_claude(limit):
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise RuntimeError("Set ANTHROPIC_API_KEY before running paid Claude evaluations.")

    resume_text = extract_resume_text()
    jobs = _load_jobs(
        """SELECT company, title, description, location, url, source, posted_at,
                  local_ai_relevant, local_ai_score, local_ai_evaluated_at
           FROM jobs WHERE ai_evaluated_at IS NULL ORDER BY id"""
    )
    eligible = [
        job
        for job in jobs
        if job["local_ai_evaluated_at"] is not None
        and job["local_ai_relevant"]
        and job["local_ai_score"] is not None
        and job["local_ai_score"] >= LOCAL_AI_THRESHOLD
    ]
    eligible = _apply_limit(eligible, limit)

    if not eligible:
        print("No unevaluated jobs currently pass the local-AI threshold.")
        return

    print(f"{len(eligible)} jobs pass local screening and are missing Claude results.")
    confirmation = input("Evaluate them with Claude? This may incur API charges. [y/N] ")
    if confirmation.strip().lower() not in ("y", "yes"):
        print("Claude backfill cancelled; no paid evaluations were sent.")
        return

    succeeded = 0
    for job in eligible:
        try:
            result = evaluate_job(job, resume_text)
            save_ai_evaluation(job["url"], result)
        except (EvaluationError, sqlite3.Error, ValueError) as error:
            print(f"CLAUDE FAILED: {job['title']}: {error}")
            continue
        succeeded += 1
        print(f"CLAUDE: {result['score']} - {job['title']}")
    print(f"Claude backfill complete: {succeeded}/{len(eligible)} evaluated.")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Backfill missing AI evaluations for jobs already in jobs.db."
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="Run Ollama for jobs without a local-AI result.",
    )
    parser.add_argument(
        "--claude",
        action="store_true",
        help="Run Claude for jobs passing local screening; prompts before paid calls.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit each selected backfill stage to this many jobs.",
    )
    args = parser.parse_args(argv)
    if not args.local and not args.claude:
        parser.error("Select at least one stage: --local and/or --claude.")
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be a positive integer.")

    try:
        if args.local:
            _backfill_local(args.limit)
        if args.claude:
            _backfill_claude(args.limit)
        if EXCEL_PATH.exists():
            sync_excel()
    except (EvaluationError, OSError, RuntimeError, sqlite3.Error) as error:
        print(f"AI backfill failed: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())