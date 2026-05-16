import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("API Key missing!")
    exit()

genai.configure(api_key=api_key)

print("Checking available models...")
try:
    models = genai.list_models()
    for m in models:
        print(f"Name: {m.name}, Methods: {m.supported_generation_methods}")
except Exception as e:
    print(f"Error listing models: {e}")

print("\nTesting gemini-1.5-flash...")
try:
    model = genai.GenerativeModel("gemini-1.5-flash")
    resp = model.generate_content("Hi")
    print(f"Success: {resp.text}")
except Exception as e:
    print(f"Failed gemini-1.5-flash: {e}")

print("\nTesting gemini-pro...")
try:
    model = genai.GenerativeModel("gemini-pro")
    resp = model.generate_content("Hi")
    print(f"Success: {resp.text}")
except Exception as e:
    print(f"Failed gemini-pro: {e}")
