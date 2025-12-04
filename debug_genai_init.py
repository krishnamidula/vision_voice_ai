# debug_genai_init.py
import traceback
from google.oauth2 import service_account

KEY_PATH = r"C:\Users\KRISHNAMIDULA K\OneDrive\.secrets\visionvoice-ai-0f7745fdbd65.json"
PROJECT_ID = "visionvoice-ai"
LOCATION = "asia-south1"
MODEL_NAME = "gemini-1.5-flash-vision"

print("KEY_PATH:", KEY_PATH)
try:
    from google import genai
    print("google.genai import: OK, version:", getattr(genai, "__version__", "unknown"))
except Exception as e:
    print("google.genai import FAILED:")
    print(e)
    raise SystemExit(1)

try:
    creds = service_account.Credentials.from_service_account_file(KEY_PATH)
    print("Loaded service account:", creds.service_account_email if hasattr(creds, "service_account_email") else "n/a")
except Exception:
    print("Failed to load service account from file:")
    traceback.print_exc()
    raise SystemExit(1)

try:
    client = genai.Client(project=PROJECT_ID, location=LOCATION, credentials=creds)
    print("Client created:", client)
except Exception:
    print("Failed to create genai.Client():")
    traceback.print_exc()

try:
    print("Attempting to get model:", MODEL_NAME)
    model = client.get_model(MODEL_NAME)
    print("Got model object:", model)
except Exception:
    print("Failed to get model:")
    traceback.print_exc()
