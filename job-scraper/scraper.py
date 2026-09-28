import argparse
from html import escape, unescape

from greenhouse import get_jobs as greenhouse_jobs
from lever import get_jobs as lever_jobs
from ashby import get_jobs as ashby_jobs
from database import create_database, job_exists, save_job
from ai_evaluator import EvaluationError, evaluate_job, extract_resume_text
import os
import sys

def normalize_greenhouse(job, company):
    return {
        "company": company,
        "title": job["title"],
        "description": unescape(job.get("content") or ""),
        "location": job["location"]["name"],
        "url": job["absolute_url"],
        "source": "greenhouse",
        "posted_at": job.get("updated_at")
    }


def normalize_lever(job, company):
    description_parts = [
        job.get("opening", ""),
        job.get("description") or job.get("descriptionBody") or job.get("descriptionPlain", ""),
    ]
    for section in job.get("lists") or []:
        if section.get("text"):
            description_parts.append(f"<h3>{escape(section['text'])}</h3>")
        description_parts.append(section.get("content") or section.get("contentPlain", ""))
    description_parts.append(job.get("additional") or job.get("additionalPlain", ""))

    return {
        "company": company,
        "title": job["text"],
        "description": "\n".join(part for part in description_parts if part),
        "location": job["categories"].get("location", ""),
        "url": job["hostedUrl"],
        "source": "lever",
        "posted_at": None
    }


def normalize_ashby(job, company):
    return {
        "company": company,
        "title": job["title"],
        "description": job.get("descriptionHtml") or job.get("descriptionPlain", ""),
        "location": job.get("location", ""),
        "url": job.get("jobUrl"),
        "source": "ashby",
        "posted_at": None
    }

def is_cs_internship(job):

    title = job["title"].lower()

    internship_words = [
        "intern",
        "internship"
    ]

    cs_keywords = [
        "software",
        "computer science",
        "data science",
        "machine learning",
        "artificial intelligence",
        "ai ",
        "developer",
        "programming",
        "web development",
        "software development"
    ]

    has_internship = any(
        word in title
        for word in internship_words
    )

    has_cs_keyword = any(
        word in title
        for word in cs_keywords
    )

    return has_internship and has_cs_keyword

greenhouse_companies = [
    "stripe",
    "datadog",
    "anthropic",
    "gusto",
    "waymo",
    "htrading",
    "cloudflare",
    "figma",
    "notion",
]

lever_companies = [
    "netflix",
    "spotify",
    "roblox",
    "discord",
    "palantir",
]

ashby_companies = [
    "replit",
    "beaconsoftware",
    "junior",
    "gigaml",
    "golinks",
    "netic",
    "zettabyte-space",
]

def process_jobs(jobs, company, normalize_job, resume_text=None, evaluate_with_ai=True):
    for job in jobs:
        normalized = normalize_job(job, company)

        if not is_cs_internship(normalized):
            continue

        if job_exists(normalized["url"]):
            print(f"Duplicate skipped: {normalized['title']}")
            continue

        if evaluate_with_ai:
            try:
                evaluation = evaluate_job(normalized, resume_text)
            except EvaluationError as error:
                print(f"AI evaluation failed for {normalized['title']}: {error}")
                continue
        else:
            evaluation = None

        is_new = save_job(normalized, evaluation)
        if is_new:
            print(f"NEW JOB: {normalized['title']}")
            if evaluation is not None:
                print(f"AI Score: {evaluation['score']}\n")
        else:
            print(f"Duplicate skipped: {normalized['title']}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Scrape and save CS internship postings.")
    parser.add_argument(
        "--no-ai",
        action="store_true",
        help="Save filtered jobs to SQLite without evaluating them with the AI API.",
    )
    args = parser.parse_args(argv)

    create_database()

    resume_text = None
    if not args.no_ai:
        if not os.getenv("ANTHROPIC_API_KEY"):
            print("Error: ANTHROPIC_API_KEY is not set.", file=sys.stderr)
            return 1

        try:
            resume_text = extract_resume_text()
        except EvaluationError as error:
            print(f"Error: {error}", file=sys.stderr)
            return 1

    for company in greenhouse_companies:
        print(f"Checking Greenhouse: {company}")
        process_jobs(
            greenhouse_jobs(company),
            company,
            normalize_greenhouse,
            resume_text,
            evaluate_with_ai=not args.no_ai,
        )

    for company in lever_companies:
        print(f"Checking Lever: {company}")
        process_jobs(
            lever_jobs(company),
            company,
            normalize_lever,
            resume_text,
            evaluate_with_ai=not args.no_ai,
        )

    for company in ashby_companies:
        print(f"Checking Ashby: {company}")
        process_jobs(
            ashby_jobs(company),
            company,
            normalize_ashby,
            resume_text,
            evaluate_with_ai=not args.no_ai,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
