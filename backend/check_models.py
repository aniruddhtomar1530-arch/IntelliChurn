import os
from dotenv import load_dotenv
from google import genai

# Load API key from .env
load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

print("✅ Available Models for your API Key:")
for model in client.models.list():
    print(f" - {model.name}")