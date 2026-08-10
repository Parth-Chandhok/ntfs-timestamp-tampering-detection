import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

MODEL = "gemini-3.5-flash"

resp = client.models.generate_content(
    model=MODEL,
    contents="Reply with exactly: HARNESS OK",
    config=types.GenerateContentConfig(temperature=0),
)
print(f"model : {MODEL}")
print(f"reply : {resp.text.strip()}")
print(f"tokens: in={resp.usage_metadata.prompt_token_count} "
      f"out={resp.usage_metadata.candidates_token_count}")