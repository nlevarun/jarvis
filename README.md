# J.A.R.V.I.S.

A lightweight Python-based conversational assistant that embodies Tony Stark's personal AI, **J.A.R.V.I.S.** (Just A Rather Very Intelligent System). Powered by the Groq API, this assistant features a witty persona and automatic real-time web-searching capabilities.

## Features

* **Smart Web Search Routing**: Automatically detects when a user's prompt requires real-time or up-to-date information (e.g., "What's the weather today?", "Recent news") and fetches results instantly using DuckDuckGo.
* **Context Retention**: Maintains conversation history for multi-turn dialogues while keeping the contextual payload clean of web-search bloat.
* **Powered by Groq**: Optimized to use high-throughput LLM architectures via the Groq SDK.

## Prerequisites

Ensure you have Python 3.8+ installed along with a **Groq API Key** (available from the Groq Console).

## Installation

1. Clone the repository:
   $ git clone https://github.com/nlevarun/jarvis
   $ cd jarvis

2. Install dependencies:
   $ pip install groq python-dotenv ddgs

3. Set up Environment Variables:
   Create a .env file in the root directory of your project and insert your Groq API key:
   GROQ_API_KEY=your_actual_groq_api_key_here

## Usage

You can import and interact with J.A.R.V.I.S. inside your script or an interactive Python shell:

```python
from jarvis import ask, reset_history

# General conversation
response = ask("Hello J.A.R.V.I.S., how are you today?")
print(response)
# Output: "Splendid as always, sir. Ready to assist with whatever you have planned."

# Query needing live search data
response_search = ask("What is the current stock price of Apple?")
print(response_search)
# [Search] What is the current stock price of Apple?
# Output: "Apple is currently trading at..."

# Reset conversation memory if needed
reset_history()