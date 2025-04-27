from google import genai
import os

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def get_intelligent_response(prompt: str) -> str:
    response = client.models.generate_content(
        model="gemini-2.5-pro-preview-03-25",
        contents=prompt,
    )
    return response.text