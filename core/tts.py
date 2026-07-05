import subprocess

TTS_VOICE   = "Daniel"
_current    = None

def speak(text: str, voice: str = TTS_VOICE):
    global _current
    clean = text.replace('"', '').replace("'", "").strip()
    if not clean:
        return
    # kill previous speech before starting new one
    stop()
    _current = subprocess.Popen(["say", "-v", voice, clean])

def stop():
    global _current
    if _current and _current.poll() is None:
        _current.terminate()
        _current = None