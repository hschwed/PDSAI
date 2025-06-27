import requests

url = "http://18.135.72.18/api/v1/"
headers = {
    "Authorization": "Bearer "
}

response = requests.get(url, headers=headers)

print(response.status_code)
print(response.json())  # or response.text if it's not JSON
