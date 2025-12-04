# test_elevenlabs.py — debug + forced load
import os
from dotenv import load_dotenv
import requests
import base64
import sys

# Use absolute path to your .env file — adjust if your username or path differs
DOTENV_PATH = r"C:\Users\KRISHNAMIDULA K\OneDrive\visionvoice-backend\.env"

print("DEBUG: running from cwd:", os.getcwd())
print("DEBUG: forcing load_dotenv from:", DOTENV_PATH)
loaded = load_dotenv(dotenv_path=DOTENV_PATH, override=True)
print("DEBUG: load_dotenv returned:", loaded)

API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")  # default if absent

# Show safe preview (do NOT paste full key anywhere)
print("DEBUG: ELEVENLABS_API_KEY present?", bool(API_KEY))
print("DEBUG: ELEVENLABS_API_KEY preview:", (API_KEY or "")[:8] + ("..." if API_KEY else ""))
print("DEBUG: ELEVENLABS_VOICE_ID ->", VOICE_ID)

if not API_KEY:
    print("\n❌ ELEVENLABS_API_KEY is NOT loaded! Aborting ElevenLabs call.")
    print("Make sure the .env file contains a line like:")
    print("  ELEVENLABS_API_KEY=sk_...")
    print("Or run: Set-Content -Path .env -Value 'ELEVENLABS_API_KEY=sk-...'")
    sys.exit(1)

# Make the TTS request
url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
headers = {
    "Accept": "audio/mpeg",
    "Content-Type": "application/json",
    "xi-api-key": API_KEY,
}
payload = {"text": "Hello Krishna! ElevenLabs connection test successful.", "model_id": "eleven_multilingual_v2"}

print("\nDEBUG: Sending request to ElevenLabs...")
try:
    resp = requests.post(url, json=payload, headers=headers, timeout=30)
except Exception as e:
    print("❌ Network/requests exception:", str(e))
    sys.exit(1)

print("DEBUG: HTTP status:", resp.status_code)
ct = resp.headers.get("content-type","")
print("DEBUG: content-type:", ct)

if resp.status_code != 200:
    print("❌ ElevenLabs returned non-200:")
    # show short message (safe) for debugging
    text = resp.text
    print(text[:1000])
    sys.exit(1)

# Save returned audio to file
out_path = "elevenlabs_test.mp3"
with open(out_path, "wb") as f:
    f.write(resp.content)

print("✔ Success — saved audio to", out_path)
