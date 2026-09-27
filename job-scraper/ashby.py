import requests


def get_jobs(company):
    url = f"https://api.ashbyhq.com/posting-api/job-board/{company}"

    response = requests.get(url)

    if response.status_code != 200:
        print(f"{company}: Ashby board not found")
        return []

    data = response.json()

    return data["jobs"]


if __name__ == "__main__":
    jobs = get_jobs("Ashby")

    for job in jobs[:5]:
        print(job["title"])
        print(job.get("location"))
        print(job.get("employmentType"))
        print(job.get("jobUrl"))
        print("-" * 50)