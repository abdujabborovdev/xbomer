import requests

url = "https://unsuspectingly-vigorous-natalee.ngrok-free.dev/api/v1/api/v1/"

payload = {
    "key": "f127e71118b6ab984688873d2a96e297"
}

# params o'rniga json=payload ishlatamiz
response = requests.post(url, json=payload)
print(response.status_code)
print(response.text)