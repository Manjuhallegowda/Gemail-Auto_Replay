
from openai import OpenAI
from config import OPENAI_API_KEY
from logger import get_logger
import httpx

logger = get_logger(__name__)

# Create an httpx client without explicitly setting proxies
_http_client = httpx.Client()

client = OpenAI(api_key=OPENAI_API_KEY, http_client=_http_client)

def generate_ai_reply(prompt):
    """
    Generate an AI-based reply using OpenAI's GPT-3.5-turbo.

    Args:
        prompt (str): The email content to generate a reply for.

    Returns:
        str: The AI-generated reply.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional and helpful assistant."},
                {"role": "user", "content": f"Based on the following email, write a professional and helpful reply:\n\n{prompt}\n\nReply:"}
            ],
            max_tokens=150,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"An error occurred during AI reply generation: {e}")
        return None
