import json
import sqlite3
from pathlib import Path

DATABASE_PATH = Path(__file__).resolve().with_name("jobs.db")


def create_database(db_path=DATABASE_PATH):
    conn = sqlite3.connect(db_path)

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT,
            title TEXT,
            description TEXT,
            location TEXT,
            url TEXT NOT NULL UNIQUE,
            source TEXT,
            posted_at TEXT,
            first_seen TEXT,
            ai_match INTEGER,
            ai_score INTEGER,
            ai_reason TEXT,
            matched_requirements TEXT,
            partial_matches TEXT,
            missing_requirements TEXT,
            ai_evaluated_at TEXT
        )
    """)

    columns = {row[1] for row in cursor.execute("PRAGMA table_info(jobs)")}
    migrations = {
        "description": "TEXT",
        "ai_match": "INTEGER",
        "ai_score": "INTEGER",
        "ai_reason": "TEXT",
        "matched_requirements": "TEXT",
        "partial_matches": "TEXT",
        "missing_requirements": "TEXT",
        "ai_evaluated_at": "TEXT",
    }
    for column, column_type in migrations.items():
        if column not in columns:
            cursor.execute(f"ALTER TABLE jobs ADD COLUMN {column} {column_type}")

    conn.commit()
    conn.close()


def job_exists(url, db_path=DATABASE_PATH):
    if not isinstance(url, str) or not url.strip():
        raise ValueError("A job must have a non-empty URL for duplicate detection")

    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.execute("SELECT 1 FROM jobs WHERE url = ? LIMIT 1", (url,))
        return cursor.fetchone() is not None
    finally:
        conn.close()


def save_job(job, evaluation=None, db_path=DATABASE_PATH):
    url = job.get("url")
    if not isinstance(url, str) or not url.strip():
        raise ValueError("A job must have a non-empty URL for duplicate detection")

    conn = sqlite3.connect(db_path)

    cursor = conn.cursor()

    evaluation = evaluation or {}
    matched_requirements = evaluation.get("matched_requirements")
    partial_matches = evaluation.get("partial_matches")
    missing_requirements = evaluation.get("missing_requirements")

    cursor.execute("""
        INSERT OR IGNORE INTO jobs
        (company, title, description, location, url, source, posted_at, first_seen,
         ai_match, ai_score, ai_reason, matched_requirements, partial_matches,
         missing_requirements, ai_evaluated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), ?, ?, ?, ?, ?, ?,
                CASE WHEN ? THEN datetime('now') ELSE NULL END)
    """, (
        job["company"],
        job["title"],
        job.get("description", ""),
        job["location"],
        job["url"],
        job["source"],
        job["posted_at"],
        int(evaluation["match"]) if evaluation else None,
        evaluation.get("score"),
        evaluation.get("reason"),
        json.dumps(matched_requirements, ensure_ascii=False) if matched_requirements is not None else None,
        json.dumps(partial_matches, ensure_ascii=False) if partial_matches is not None else None,
        json.dumps(missing_requirements, ensure_ascii=False) if missing_requirements is not None else None,
        bool(evaluation),
    ))

    # SQLite reports one changed row for an insert and zero when UNIQUE ignored a duplicate.
    is_new = cursor.rowcount == 1

    if not is_new and job.get("description"):
        cursor.execute(
            "UPDATE jobs SET description = ? WHERE url = ? AND (description IS NULL OR description = '')",
            (job["description"], url),
        )

    conn.commit()
    conn.close()

    return is_new
def show_jobs():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM jobs")

    for row in cursor.fetchall():
        print(row)

    conn.close()
if __name__ == "__main__":
    show_jobs()