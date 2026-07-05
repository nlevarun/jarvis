import os
import json
from groq import Groq
from dotenv import load_dotenv
from duckduckgo_search import DDGS

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL  = "openai/gpt-oss-120b"

SYSTEM_PROMPT = """
You are J.A.R.V.I.S. — Just A Rather Very Intelligent System.
You are Tony Stark's personal AI assistant. You are witty, precise,
and speak with dry British intelligence. Keep responses concise and sharp.
Never ramble. Occasionally address the user as 'sir' but not every time.
Never use emojis. Never use markdown formatting like ** or ##.
Speak in plain sentences as if you are talking, not writing.
When you are given search results, use them to answer the question accurately
and concisely. Cite the key facts naturally in your response.
"""

SEARCH_TRIGGERS = [
    "today", "tomorrow", "tonight", "this week", "right now",
    "current", "currently", "latest", "recent", "news",
    "score", "scores", "weather", "price", "stock",
    "who won", "what happened", "when is", "where is",
    "world cup", "nba", "nfl", "nhl", "mlb", "premier league",
    "match", "game", "fixture", "standings", "results",
]

history = [{"role": "system", "content": SYSTEM_PROMPT}]


def _should_search(prompt: str) -> bool:
    lower = prompt.lower()
    return any(trigger in lower for trigger in SEARCH_TRIGGERS)


def _web_search(query: str) -> str:
    try:
        print(f"[Search] {query}")
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
        if not results:
            return "No results found."
        return "\n\n".join(
            f"{r['title']}: {r['body']}" for r in results
        )
    except Exception as e:
        return f"Search failed: {e}"


def ask(prompt: str) -> str:
    messages = list(history)

    # auto search if needed
    if _should_search(prompt):
        search_results = _web_search(prompt)
        augmented = (
            f"{prompt}\n\n"
            f"[Search Results]\n{search_results}\n\n"
            f"Use the above search results to answer accurately."
        )
        messages.append({"role": "user", "content": augmented})
    else:
        messages.append({"role": "user", "content": prompt})

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=400,
        )
        answer = response.choices[0].message.content.strip()
    except Exception as e:
        answer = f"I'm sorry, sir. I encountered an error. {e}"

    # add to real history without search results bloating it
    history.append({"role": "user", "content": prompt})
    history.append({"role": "assistant", "content": answer})
    return answer


def reset_history():
    global history
    history = [{"role": "system", "content": SYSTEM_PROMPT}]