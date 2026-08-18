from google import genai
from app.config import settings

async def ask_ai(question: str, context: str = "") -> str:
    system_prompt = (
        "You are a helpful assistant for a law exam prep app in Uzbekistan. "
        "Explain legal concepts and quiz answers clearly and concisely, "
        "in the same language the user asks in."
    )
    full_prompt = system_prompt
    if context:
        full_prompt += f"\n\nRelevant context: {context}"
    full_prompt += f"\n\nQuestion: {question}"

    client = genai.Client(api_key=settings.gemini_api_key)
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=full_prompt,
    )
    return response.text