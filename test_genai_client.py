# test_genai_client.py
import traceback
from google.oauth2 import service_account

KEY_PATH = r"C:\Users\KRISHNAMIDULA K\OneDrive\.secrets\visionvoice-ai-0f7745fdbd65.json"

print("KEY_PATH:", KEY_PATH)
try:
    from google import genai
    print("google.genai import: OK")
except Exception as e:
    print("google.genai import: FAILED")
    print(e)
    raise SystemExit(1)

try:
    creds = service_account.Credentials.from_service_account_file(KEY_PATH)
    print("Service account loaded. client_email:", getattr(creds, "service_account_email", "n/a"))
except Exception as e:
    print("Failed to load service account from file:")
    traceback.print_exc()
    raise SystemExit(1)

try:
    client = genai.Client(
        model="gemini-1.5-flash-vision",
        project="visionvoice-ai",
        location="asia-south1",
        credentials=creds
    )
    print("GenAI client created:", client)
except Exception as e:
    print("Failed to create genai.Client():")
    traceback.print_exc()
