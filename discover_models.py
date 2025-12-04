from google.cloud.aiplatform_v1.services.publisher_model_service import PublisherModelServiceClient
from google.oauth2 import service_account

PROJECT_ID = "visionvoice-ai"
LOCATION = "us-central1"   # Google Gemini main region

KEY_PATH = r"C:\Users\KRISHNAMIDULA K\OneDrive\.secrets\visionvoice-ai-0f7745fdbd65.json"

print("Loading credentials from:", KEY_PATH)

creds = service_account.Credentials.from_service_account_file(KEY_PATH)

client = PublisherModelServiceClient(credentials=creds)

parent = f"projects/{PROJECT_ID}/locations/{LOCATION}/publishers/google"

print("\n🔍 Checking available publisher models...\n")

try:
    models = client.list_publisher_models(parent=parent)

    count = 0
    for m in models:
        print("MODEL NAME:", m.name)
        print("DISPLAY NAME:", m.display_name)
        print("----")
        count += 1

    print(f"\nTotal models found: {count}")

except Exception as e:
    print("\n❌ ERROR listing publisher models:")
    print(e)
