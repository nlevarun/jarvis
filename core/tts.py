import subprocess

TTS_VOICE = "Daniel"

def speak(text: str, voice: str = TTS_VOICE):
    """Non-blocking macOS TTS using the say command."""
    clean = text.replace('"', '').replace("'", "").strip()
    if clean:
        subprocess.Popen(["say", "-v", voice, clean])