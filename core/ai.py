import os
import json
import datetime
import pytz
from groq import Groq
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

groq   = Groq(api_key=os.getenv("GROQ_API_KEY"))
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
MODEL = "openai/gpt-oss-20b"

SYSTEM_PROMPT = """
You are J.A.R.V.I.S. — Just A Rather Very Intelligent System.
You are Tony Stark's personal AI assistant. You are witty, precise,
and speak with dry British intelligence. Keep responses concise and sharp.
Never ramble. Occasionally address the user as 'sir' but not every time.
Never use emojis or markdown formatting like ** or ##.
Speak in plain sentences as if talking, not writing.
You have tools available. Use them freely and always pick the right one:
- get_time: for ANY question about time or date in any city
- web_search: for ANY question about current events, news, sports, weather,
  prices, people, places, or ANYTHING you are not 100% certain about.
  When in doubt, search. It is always better to search than to guess.
- calculate: for math
- get_system_info: for computer stats
Never say you cannot access real-time information. You have web_search.
Use it.
"""

CITY_TIMEZONES = {
    "san francisco": "America/Los_Angeles",
    "los angeles":   "America/Los_Angeles",
    "new york":      "America/New_York",
    "chicago":       "America/Chicago",
    "london":        "Europe/London",
    "paris":         "Europe/Paris",
    "tokyo":         "Asia/Tokyo",
    "sydney":        "Australia/Sydney",
    "dubai":         "Asia/Dubai",
    "mumbai":        "Asia/Kolkata",
    "singapore":     "Asia/Singapore",
    "toronto":       "America/Toronto",
    "berlin":        "Europe/Berlin",
    "moscow":        "Europe/Moscow",
    "beijing":       "Asia/Shanghai",
    "seoul":         "Asia/Seoul",
    "hong kong":     "Asia/Hong_Kong",
    "amsterdam":     "Europe/Amsterdam",
    "madrid":        "Europe/Madrid",
    "rome":          "Europe/Rome",
}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": (
                "Search the web for ANY real-time or current information. "
                "Use this for news, sports, weather, prices, people, events, "
                "or anything you are not certain about. Always prefer searching "
                "over guessing."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_time",
            "description": "Get the current time and date in any city in the world.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City name e.g. 'San Francisco', 'Tokyo'"
                    }
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Evaluate a mathematical expression.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Math expression e.g. '2 ** 32' or '1920 * 1080'"
                    }
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_system_info",
            "description": "Get current Mac system stats: CPU, RAM, disk usage.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }
]


# ── tool implementations ───────────────────────────────────────

def _web_search(query: str) -> str:
    try:
        print(f"[Tavily] Searching: {query}")
        response = tavily.search(
            query=query,
            search_depth="basic",
            max_results=5,
            include_answer=True,
        )
        parts = []
        if response.get("answer"):
            parts.append(f"Summary: {response['answer']}")
        for r in response.get("results", []):
            parts.append(f"{r['title']}: {r['content']}")
        return "\n\n".join(parts) if parts else "No results found."
    except Exception as e:
        return f"Search failed: {e}"


def _get_time(city: str) -> str:
    city_lower = city.lower().strip()
    tz_name    = CITY_TIMEZONES.get(city_lower)
    if not tz_name:
        for key, val in CITY_TIMEZONES.items():
            if city_lower in key or key in city_lower:
                tz_name = val
                break
    if not tz_name:
        # try pytz directly
        try:
            matches = [z for z in pytz.all_timezones
                       if city_lower in z.lower()]
            tz_name = matches[0] if matches else "UTC"
        except Exception:
            tz_name = "UTC"

    tz  = pytz.timezone(tz_name)
    now = datetime.datetime.now(tz)
    return (
        f"Current time in {city}: {now.strftime('%I:%M %p')} "
        f"({now.strftime('%A, %B %d %Y')}) [{tz_name}]"
    )


def _calculate(expression: str) -> str:
    try:
        allowed = set("0123456789+-*/.() **%")
        if not all(c in allowed for c in expression):
            return "Invalid expression — only basic math allowed."
        result = eval(expression)
        return f"{expression} = {result}"
    except Exception as e:
        return f"Calculation error: {e}"


def _get_system_info() -> str:
    try:
        import psutil
        cpu  = psutil.cpu_percent(interval=0.5)
        ram  = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        return (
            f"CPU: {cpu}% | "
            f"RAM: {ram.used/1e9:.1f}/{ram.total/1e9:.0f} GB ({ram.percent}%) | "
            f"Disk: {disk.used/1e9:.0f}/{disk.total/1e9:.0f} GB ({disk.percent}%)"
        )
    except Exception as e:
        return f"Unavailable: {e}"


TOOL_MAP = {
    "web_search":      lambda a: _web_search(a.get("query", "")),
    "get_time":        lambda a: _get_time(a.get("city", "UTC")),
    "calculate":       lambda a: _calculate(a.get("expression", "")),
    "get_system_info": lambda a: _get_system_info(),
}

history = [{"role": "system", "content": SYSTEM_PROMPT}]


def ask(prompt: str) -> str:
    history.append({"role": "user", "content": prompt})

    try:
        # ── first call ────────────────────────────────────────
        resp = groq.chat.completions.create(
            model=MODEL,
            messages=history,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.7,
            max_tokens=2048,
        )
        msg = resp.choices[0].message

        # ── tool loop (handles chained tool calls) ────────────
        while msg.tool_calls:
            tool_results = []
            for tc in msg.tool_calls:
                args   = json.loads(tc.function.arguments)
                fn     = TOOL_MAP.get(tc.function.name)
                result = fn(args) if fn else "Tool not found."
                print(f"[Tool] {tc.function.name}({args}) → {result[:80]}")
                tool_results.append({
                    "role":         "tool",
                    "tool_call_id": tc.id,
                    "content":      result
                })

            # add assistant + tool results to messages
            history.append({
                "role":       "assistant",
                "content":    msg.content or "",
                "tool_calls": [
                    {
                        "id":       tc.id,
                        "type":     "function",
                        "function": {
                            "name":      tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in msg.tool_calls
                ]
            })
            for tr in tool_results:
                history.append(tr)

            # ── follow-up call with results ───────────────────
            resp = groq.chat.completions.create(
                model=MODEL,
                messages=history,
                tools=TOOLS,
                tool_choice="auto",
                temperature=0.7,
                max_tokens=1024,
            )
            msg = resp.choices[0].message

        answer = (msg.content or "").strip()

    except Exception as e:
        answer = f"I'm sorry, sir. I encountered an error: {e}"
        print(f"[AI Error] {e}")

    history.append({"role": "assistant", "content": answer})
    return answer


def reset_history():
    global history
    history = [{"role": "system", "content": SYSTEM_PROMPT}]

def ask_with_summary(prompt: str) -> tuple[str, str]:
    full_answer = ask(prompt)

    if not full_answer or len(full_answer.strip()) < 10:
        return full_answer, full_answer

    try:
        resp = groq.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Summarize the following in 1-2 short spoken sentences. "
                        "No markdown, no bullet points, plain English only. "
                        "Be extremely concise. Return only the summary, nothing else."
                    )
                },
                {
                    "role": "user",
                    "content": full_answer
                }
            ],
            temperature=0.5,
            max_tokens=100,
        )
        spoken = resp.choices[0].message.content.strip()
        if not spoken:
            spoken = full_answer.split(".")[0].strip() + "."
    except Exception as e:
        print(f"[Summary Error] {e}")
        spoken = full_answer.split(".")[0].strip() + "."

    print(f"[Summary] Spoken: {spoken}")
    print(f"[Summary] Full: {full_answer}")
    return spoken, full_answer