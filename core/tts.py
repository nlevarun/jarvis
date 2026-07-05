import os
import threading
import tempfile
import subprocess
from elevenlabs import ElevenLabs
from dotenv import load_dotenv

load_dotenv()

client   = ElevenLabs(api_key=os.getenv("ELEVEN_LABS_API_KEY"))
VOICE_ID = "onwK4e9ZLuTAKqWW03F9"
MODEL_ID = "eleven_turbo_v2_5"

_current_process = None
_lock            = threading.Lock()


def speak(text: str, voice_id: str = VOICE_ID):
    global _current_process
    stop()

    def _run():
        global _current_process
        try:
            print("[TTS] Generating...")
            audio_stream = client.text_to_speech.convert(
                text=text,
                voice_id=voice_id,
                model_id=MODEL_ID,
                output_format="mp3_44100_128",
            )
            chunks = b"".join(audio_stream)
            print(f"[TTS] Playing {len(chunks)} bytes...")

            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                f.write(chunks)
                tmp_path = f.name

            with _lock:
                _current_process = subprocess.Popen(
                    ["afplay", tmp_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            _current_process.wait()
            os.unlink(tmp_path)
            print("[TTS] Done.")

        except Exception as e:
            print(f"[TTS Error] {e}")

    threading.Thread(target=_run, daemon=True).start()


def stop():
    global _current_process
    with _lock:
        if _current_process and _current_process.poll() is None:
            _current_process.terminate()
            _current_process = None