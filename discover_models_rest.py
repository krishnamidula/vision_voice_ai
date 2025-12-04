# discover_models_rest.py
import json
import os
from google.oauth2 import service_account
from google.auth.transport.requests import Request
import requests

PROJECT_ID = "visionvoice-ai"
LOCATION = "us-central1"   # try us-central1 (change if you want)
KEY_PATH = r"C:\Users\KRISHNAMIDULA K\OneDrive\.secrets\visionvoice-ai-0f7745fdbd65.json"

print("Using key:", KEY_PATH)
if not os.path.exists(KEY_PATH):
    print("ERROR: key file not found at path:", KEY_PATH)
    raise SystemExit(1)

# create credentials with cloud-platform scope and refresh to get access token
creds = service_account.Credentials.from_service_account_file(
    KEY_PATH,
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)
creds.refresh(Request())
token = creds.token
print("Obtained access token (masked):", token[:20] + "..." if token else "NO_TOKEN")

# REST endpoint for publisher models listing
base = f"https://{LOCATION}-aiplatform.googleapis.com/v1"
url = f"{base}/projects/{PROJECT_ID}/locations/{LOCATION}/publishers/google/models"

headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/json"
}

print("\nCalling:", url)
resp = requests.get(url, headers=headers, timeout=30)

print("\nHTTP status:", resp.status_code)
try:
    data = resp.json()
    print(json.dumps(data, indent=2))
except Exception:
    print("Non-JSON response body:")
    print(resp.text)
