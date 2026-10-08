import requests

response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "tev1:4b",
        "prompt": "Is a Software Engineering Intern position relevant to a Computer Science student? Answer yes or no and explain briefly.",
        "stream": False
    }
)

print(response.json()["response"])