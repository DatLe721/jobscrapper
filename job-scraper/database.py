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
            first_seen TEXT
        )
    """)

    columns = {row[1] for row in cursor.execute("PRAGMA table_info(jobs)")}
    if "description" not in columns:
        cursor.execute("ALTER TABLE jobs ADD COLUMN description TEXT")

    conn.commit()
    conn.close()


def save_job(job, db_path=DATABASE_PATH):
    url = job.get("url")
    if not isinstance(url, str) or not url.strip():
        raise ValueError("A job must have a non-empty URL for duplicate detection")

    conn = sqlite3.connect(db_path)

    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO jobs
        (company, title, description, location, url, source, posted_at, first_seen)
        VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
    """, (
        job["company"],
        job["title"],
        job.get("description", ""),
        job["location"],
        job["url"],
        job["source"],
        job["posted_at"]
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