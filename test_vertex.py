# test_vertex.py
from google.cloud import aiplatform
import os

# Ensure these match your project and preferred location:
PROJECT_ID = "visionvoice-ai"
LOCATION = "asia-south1"   # you chose this earlier

# Initialize client
aiplatform.init(project=PROJECT_ID, location=LOCATION)

# List models (will show models available in the selected location)
models = aiplatform.Model.list()
print(f"Found {len(models)} models.")
for m in models:
    # Print only a few useful fields for now
    print(m.resource_name, "| display_name:", getattr(m, "display_name", "n/a"))
