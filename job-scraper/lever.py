import requests


def get_jobs(company):
    url = f"https://api.lever.co/v0/postings/{company}?mode=json"

    response = requests.get(url)

    if response.status_code != 200:
        print(f"{company}: Lever board not found")
        return []

    return response.json()


if __name__ == "__main__":
    jobs = get_jobs("netflix")

    for job in jobs[:5]:
        print(job["text"])
        print(job["categories"]["location"])
        print(job["hostedUrl"])
        print("-" * 50)