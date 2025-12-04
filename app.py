# app.py — VisionVoice AI (friendly narration, ElevenLabs TTS with personality, caching)
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv
import os, traceback, base64, hashlib, time, io
import requests

from google.cloud import vision
from google.oauth2 import service_account

# load .env
load_dotenv()

app = Flask(__name__)
CORS(app)

# configuration
KEY_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")

# Cache directory for synthesized audio
CACHE_DIR = os.path.join(os.path.dirname(__file__), "tts_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

# ---------------- ElevenLabs TTS helper with personality + caching ----------------
def narration_cache_path(narration: str) -> str:
    key = hashlib.sha256(narration.encode("utf-8")).hexdigest()
    return os.path.join(CACHE_DIR, f"{key}.mp3")

def elevenlabs_tts_synthesize(narration: str, voice_id: str = None) -> bytes:
    """
    Synthesize `narration` using ElevenLabs and return mp3 bytes.
    Caches result in CACHE_DIR to avoid repeated calls.
    """
    if voice_id is None:
        voice_id = ELEVENLABS_VOICE_ID
    if not ELEVENLABS_API_KEY or not voice_id:
        raise RuntimeError("ElevenLabs API key or voice id not configured.")

    # caching
    cache_path = narration_cache_path(narration)
    if os.path.exists(cache_path):
        with open(cache_path, "rb") as f:
            return f.read()

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg"
    }

    # Personality settings — tune for friendliness and clarity
    payload = {
        "text": narration,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.55,        # smoothness
            "similarity_boost": 0.7   # character similarity
        }
    }

    resp = requests.post(url, json=payload, headers=headers, timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(f"ElevenLabs TTS failed: {resp.status_code} {resp.text}")

    audio_bytes = resp.content
    # save to cache
    with open(cache_path, "wb") as f:
        f.write(audio_bytes)
    return audio_bytes

# ---------------- Helpers for narration ----------------
def pct_str(score):
    if score is None:
        return None
    return f"about {int(round(score * 100))}%"

def bbox_props(bbox):
    try:
        verts = []
        if hasattr(bbox, "normalized_vertices") and bbox.normalized_vertices:
            verts = [(v.x, v.y) for v in bbox.normalized_vertices if v is not None]
        elif hasattr(bbox, "vertices") and bbox.vertices:
            verts = [(v.x, v.y) for v in bbox.vertices if v is not None]
        if not verts:
            return None
        xs = [x for x, y in verts if x is not None]
        ys = [y for x, y in verts if y is not None]
        cx = sum(xs) / len(xs)
        cy = sum(ys) / len(ys)
        width = max(xs) - min(xs) if xs else 0
        height = max(ys) - min(ys) if ys else 0
        area = abs(width * height)
        return {"cx": cx, "cy": cy, "area": area}
    except Exception:
        return None

def pos_str(cx):
    if cx is None:
        return None
    try:
        if cx < 0.33:
            return "left"
        if cx < 0.66:
            return "center"
        return "right"
    except Exception:
        return None

def size_str(area):
    if area is None:
        return None
    if area < 0.02:
        return "small"
    if area < 0.12:
        return "medium"
    return "large"

# ---------------- Main /vision endpoint ----------------
@app.route("/vision", methods=["POST"])
def vision_route():
    """
    Accepts multipart form with 'image' file.
    Returns JSON:
    {
      status: success/error,
      narration: "human friendly text",
      audio_b64: base64 mp3 or null,
      debug: {labels, objects, web_entities}
    }
    """
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    image_file = request.files["image"]
    image_bytes = image_file.read()

    # Load service account credentials
    try:
        creds = service_account.Credentials.from_service_account_file(
            KEY_PATH,
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
    except Exception as e:
        app.logger.error("Failed to load service account: %s", e)
        return jsonify({"status": "error", "error": str(e)}), 500

    try:
        vision_client = vision.ImageAnnotatorClient(credentials=creds)
        image = vision.Image(content=image_bytes)

        label_resp = vision_client.label_detection(image=image, max_results=8)
        object_resp = vision_client.object_localization(image=image)
        web_resp = vision_client.web_detection(image=image)

        # debug lists
        labels = [l.description for l in (label_resp.label_annotations or [])][:6]
        objects_raw = object_resp.localized_object_annotations or []
        objects = [
            {"name": obj.name, "score": float(obj.score) if hasattr(obj, "score") else None, "bbox": getattr(obj, "bounding_poly", None)}
            for obj in objects_raw
        ]

        web_entities = []
        if web_resp.web_detection and web_resp.web_detection.web_entities:
            seen = set()
            for e in web_resp.web_detection.web_entities:
                if e.description:
                    d = e.description.strip()
                    if d.lower() not in seen:
                        seen.add(d.lower())
                        web_entities.append(d)
                if len(web_entities) >= 4:
                    break

        # Compose friendly narration
        narration_sentences = []

        # Safety-critical keywords to push priority and alert wording
        danger_keywords = {"vehicle", "car", "truck", "motorcycle", "stair", "stairs", "knife", "fire", "flame", "smoke"}

        if objects:
            ranked = sorted(objects, key=lambda o: (o["score"] is not None, o["score"] or 0), reverse=True)
            top = ranked[:3]
            obj_phrases = []
            danger_alerts = []
            for o in top:
                nm = (o["name"] or "object").lower()
                props = bbox_props(o.get("bbox"))
                position = pos_str(props["cx"]) if props else None
                size = size_str(props["area"]) if props else None
                article = "an" if nm[0] in "aeiou" else "a"
                parts = [f"{article} {nm}"]
                if position:
                    parts.append(f"on the {position}")
                if size:
                    parts.append(f"({size})")
                # only include confidence when ambiguous (<0.8)
                if o.get("score") is not None and o.get("score") < 0.8:
                    parts.append(f"— I'm {pct_str(o.get('score'))} sure")
                phrase = " ".join(parts)
                obj_phrases.append(phrase)
                # danger check
                for dk in danger_keywords:
                    if dk in nm:
                        danger_alerts.append(nm)
            # Build narration
            if len(obj_phrases) == 1:
                narration_sentences.append(f"I see {obj_phrases[0]}.")
            else:
                narration_sentences.append("I see " + ", and ".join(obj_phrases) + ".")
            if danger_alerts:
                # unique
                uniq = ", ".join(sorted(set(danger_alerts)))
                narration_sentences.append(f"Warning: detected {uniq}. Please be careful.")
        elif labels:
            clean_labels = []
            seen = set()
            for l in labels:
                ll = l.strip().lower()
                if ll not in seen:
                    seen.add(ll)
                    clean_labels.append(ll)
            if clean_labels:
                narration_sentences.append("This image likely contains " + ", ".join(clean_labels[:4]) + ".")

        if web_entities:
            narration_sentences.append("These look similar to " + ", ".join(web_entities[:3]) + ".")

        if not narration_sentences:
            narration_sentences.append("I can see an object, but I'm not sure what it is.")

        # Final narration
        narration = " ".join(s.strip() for s in narration_sentences).strip()
        if len(narration) > 350:
            narration = narration[:345].rsplit(" ", 1)[0] + "."

        # Prepend a friendly session intro once per request (short)
        session_intro = "Hello! "  # keep short to save TTS cost/time
        narration_for_tts = session_intro + narration

        # Synthesize audio (use caching)
        audio_b64 = None
        try:
            if ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID:
                audio_bytes = elevenlabs_tts_synthesize(narration_for_tts)
                audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        except Exception as tts_err:
            app.logger.warning("ElevenLabs TTS failed: %s", str(tts_err))
            audio_b64 = None

        return jsonify({
            "status": "success",
            "narration": narration,
            "audio_b64": audio_b64,
            "debug": {
                "labels": labels,
                "objects": [{"name": o["name"], "score": o["score"]} for o in objects],
                "web_entities": web_entities
            }
        }), 200

    except Exception as e:
        app.logger.error("Vision API failed: %s", e)
        app.logger.debug(traceback.format_exc())
        return jsonify({
            "status": "error",
            "narration": "Fallback: I see an object on a surface.",
            "error": str(e)
        }), 500

# Health route
@app.route("/")
def home():
    return jsonify({"message": "VisionVoice AI backend is running!"})

# Run app
if __name__ == "__main__":
    print("Using KEY_PATH:", KEY_PATH)
    print("ELEVENLABS_API_KEY present:", bool(ELEVENLABS_API_KEY))
    print("ELEVENLABS_VOICE_ID present:", bool(ELEVENLABS_VOICE_ID))
    app.run(host="0.0.0.0", port=5000, debug=True)
