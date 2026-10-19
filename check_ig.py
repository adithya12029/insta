import os
import requests
from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
PAGE_ID = os.getenv("INSTAGRAM_PAGE_ID", "")

# Query the page for its connected Instagram Business Account
url = f"https://graph.facebook.com/v19.0/{PAGE_ID}?fields=instagram_business_account"
response = requests.get(url, params={"access_token": ACCESS_TOKEN}).json()

print("API Response:", response)
