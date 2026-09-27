import requests
from datetime import datetime, timedelta, timezone



def get_jobs(company):
    url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs"

    response = requests.get(url, params={"content": "true"})

    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return []

    data = response.json()
    
    return data["jobs"]


def is_recent(job):
    posted_time = datetime.fromisoformat(
        job["updated_at"].replace("Z", "+00:00")
    )

    now = datetime.now(timezone.utc)

    return now - posted_time < timedelta(hours=24)


def is_cs_internship(job):
    title = job["title"].lower()

    keywords = [
        "software",
        "computer science",
        "data science",
        "machine learning",
        "artificial intelligence",
        "ai ",
        "developer",
        "programming",
    ]

    internship_words = [
        "intern",
        "internship",
    ]

    has_internship = any(word in title for word in internship_words)
    has_cs_keyword = any(word in title for word in keywords)

    return has_internship and has_cs_keyword


companies = [
    "stripe",
    "datadog",
    "anthropic",
    "airbnb",
    "figma",
    "notion",
    "coinbase",
    "cloudflare",
]

if __name__ == "__main__":
    for company in companies:
        print(f"\nChecking {company}...")

        jobs = get_jobs(company)

        for job in jobs:
            if is_recent(job) and is_cs_internship(job):
                print("TITLE:", job["title"])
                print("LOCATION:", job["location"]["name"])
                print("UPDATED:", job["updated_at"])
                print("URL:", job["absolute_url"])
                print("-" * 50)
            else:
                print("No recent CS internship found for this job.")
                print("-" * 50)