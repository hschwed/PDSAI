import requests

url = "http://18.135.72.18/api/v1/"
headers = {
    "Authorization": "Bearer 13219f917a38bb6c79962f15623dc176"
}

response = requests.get(url, headers=headers)

print(response.status_code)
print(response.json())  # or response.text if it's not JSON
