from greenhouse import get_jobs as greenhouse_jobs
from lever import get_jobs as lever_jobs
from ashby import get_jobs as ashby_jobs
from database import create_database, save_job

def normalize_greenhouse(job, company):
    return {
        "company": company,
        "title": job["title"],
        "location": job["location"]["name"],
        "url": job["absolute_url"],
        "source": "greenhouse",
        "posted_at": job.get("updated_at")
    }


def normalize_lever(job, company):
    return {
        "company": company,
        "title": job["text"],
        "location": job["categories"].get("location", ""),
        "url": job["hostedUrl"],
        "source": "lever",
        "posted_at": None
    }


def normalize_ashby(job, company):
    return {
        "company": company,
        "title": job["title"],
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

new_jobs = []


def process_jobs(jobs, company, normalize_job):
    for job in jobs:
        normalized = normalize_job(job, company)

        if not is_cs_internship(normalized):
            continue

        # Only save_job's True result means this URL was inserted for the first time.
        is_new = save_job(normalized)
        if is_new:
            new_jobs.append(normalized)
            print(f"NEW: {company} - {normalized['title']}")
        else:
            print(f"DUPLICATE: {company} - {normalized['title']}")

create_database()
for company in greenhouse_companies:

    print(f"Checking Greenhouse: {company}")

    jobs = greenhouse_jobs(company)
    process_jobs(jobs, company, normalize_greenhouse)


for company in lever_companies:

    print(f"Checking Lever: {company}")

    jobs = lever_jobs(company)
    process_jobs(jobs, company, normalize_lever)

for company in ashby_companies:

    print(f"Checking Ashby: {company}")

    jobs = ashby_jobs(company)
    process_jobs(jobs, company, normalize_ashby)

print("\nNEW JOBS")
print("=" * 60)

if not new_jobs:
    print("No new matching jobs found.")

for job in new_jobs:

    print("COMPANY:", job["company"])
    print("TITLE:", job["title"])
    print("LOCATION:", job["location"])
    print("SOURCE:", job["source"])
    print("URL:", job["url"])
    print("-" * 60)

