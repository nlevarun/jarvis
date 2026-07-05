# J.A.R.V.I.S.
### Just A Rather Very Intelligent System

A Python-based conversational AI assistant that embodies Tony Stark's personal AI. Featuring a full sci-fi HUD interface, real-time web search, voice activation, and a British ElevenLabs voice — J.A.R.V.I.S. is built to feel like the real thing.

---

## Features

- **Full HUD Interface** — Sci-fi dashboard built with PySide6, featuring a live arc reactor animation, system stats (CPU, RAM, disk, network), world clock, AI status panel, and a live response terminal
- **Wake Word Activation** — Say "Hey Jarvis" to open a voice session. Jarvis listens continuously until 30 seconds of silence, then closes the session automatically
- **ElevenLabs Voice** — High-quality British TTS voice powered by ElevenLabs, with short spoken summaries and full written responses displayed in the UI
- **Real-Time Web Search** — Powered by Tavily API for accurate, up-to-date information on news, sports, weather, and more
- **Tool Calling** — Jarvis autonomously decides when to search the web, check the time in any city, run calculations, or read system stats
- **Context Retention** — Maintains full conversation history for natural multi-turn dialogue
- **Powered by Groq** — Ultra-fast LLM inference via the Groq API

---

## Prerequisites

- Python 3.10+
- A microphone (iPhone via Continuity Camera works great)
- API keys for Groq, Tavily, and ElevenLabs

---

## Installation

1. Clone the repository:
```bash
git clone https://github.com/nlevarun/jarvis
cd jarvis
```

2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up your `.env` file in the root directory:
```env
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
ELEVEN_LABS_API_KEY=your_elevenlabs_api_key
```

---

## Usage

Run the full HUD interface:
```bash
python3 main.py
```

Or interact via Python directly:
```python
from core.ai import ask, ask_with_summary, reset_history

# General conversation
response = ask("Hello J.A.R.V.I.S., how are you today?")
print(response)

# Get both spoken summary and full answer
spoken, full = ask_with_summary("What NBA games are on today?")
print("Spoken:", spoken)
print("Full:", full)

# Reset conversation memory
reset_history()
```

---

## Voice Commands

| Action | How |
|---|---|
| Activate Jarvis | Say "Hey Jarvis" |
| Ask anything | Speak naturally after wake word |
| Follow-up questions | No need to repeat wake word during session |
| Session closes | Automatically after 30s of silence |

---

## Project Structure

```
jarvis/
├── core/
│   ├── ai.py          # Groq LLM, tool calling, Tavily search
│   ├── tts.py         # ElevenLabs text-to-speech
│   └── voice.py       # Wake word detection, voice sessions
├── ui/
│   ├── window.py      # Main HUD window
│   ├── panels.py      # System stats, AI status, tools, log panels
│   ├── reactor.py     # Arc reactor animation
│   ├── terminal.py    # Live response chat panel
│   ├── animations.py  # Waveform, voice activity, bottom bar
│   ├── background.py  # Animated circuit grid background
│   ├── widgets.py     # Top bar, reusable components
│   └── theme.py       # Colors, fonts, styles
├── main.py            # Entry point
├── .env               # API keys (never commit this)
├── .gitignore
└── requirements.txt
```

---

## API Keys

| Service | Free Tier | Get Key |
|---|---|---|
| Groq | Yes — generous limits | console.groq.com |
| Tavily | Yes — 1000 searches/month | tavily.com |
| ElevenLabs | Yes — 10k chars/month | elevenlabs.io |

---

## Built With

- [Groq](https://groq.com) — LLM inference
- [Tavily](https://tavily.com) — Real-time web search
- [ElevenLabs](https://elevenlabs.io) — Text to speech
- [PySide6](https://doc.qt.io/qtforpython/) — GUI framework
- [SpeechRecognition](https://pypi.org/project/SpeechRecognition/) — Voice input
- [psutil](https://pypi.org/project/psutil/) — System stats

---

*"Sometimes you gotta run before you can walk." — Tony Stark*