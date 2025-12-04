# upload_test.py
import requests
from pathlib import Path

# make sure your backend is running at http://127.0.0.1:5000
URL = "http://127.0.0.1:5000/vision"

# <-- change this path only if your file is somewhere else
IMAGE_PATH = r"C:\Users\KRISHNAMIDULA K\OneDrive\Attachments\download.jpeg"

p = Path(IMAGE_PATH)
if not p.exists():
    print("File not found:", IMAGE_PATH)
else:
    with p.open("rb") as f:
        files = {"image": (p.name, f, "image/jpeg")}
        try:
            resp = requests.post(URL, files=files, timeout=60)
            print("Status code:", resp.status_code)
            print("Response body:")
            print(resp.text)
        except Exception as e:
            print("Request failed:", e)
