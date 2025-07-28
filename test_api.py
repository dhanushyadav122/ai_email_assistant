import requests

OPENROUTER_API_KEY = "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"

headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json"
}

data = {
    "model": "mistralai/mistral-7b-instruct",
    "messages": [
        {"role": "user", "content": "Write a polite email to my boss explaining a delay due to illness."}
    ]
}

response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)

print("Status Code:", response.status_code)
print("Response:", response.json())
