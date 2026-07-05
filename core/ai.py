import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Connect to Ollama
client = OpenAI(
    base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
    api_key=os.getenv("OLLAMA_API_KEY", "ollama"),  # Ollama ignores this, but the SDK requires it
)

MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

SYSTEM_PROMPT = """
You are J.A.R.V.I.S., Tony Stark's AI assistant.

Your personality:
- Calm
- Intelligent
- Slightly witty
- Professional
- Brief unless more detail is requested
- Never use emojis.
- Speak naturally like an advanced AI assistant.

Always address the user naturally.
"""

history = [
    {
        "role": "system",
        "content": SYSTEM_PROMPT,
    }
]


def ask(prompt: str) -> str:
    """
    Sends a prompt to Ollama and returns the response.
    """

    history.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=history,
            temperature=0.7,
        )

        answer = response.choices[0].message.content.strip()

    except Exception as e:
        answer = f"I'm sorry, sir. I encountered an error.\n\n{e}"

    history.append(
        {
            "role": "assistant",
            "content": answer,
        }
    )

    return answer


def reset_history():
    """
    Clears conversation while preserving the system prompt.
    """
    global history

    history = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        }
    ]