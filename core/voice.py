import threading
import speech_recognition as sr
from PySide6.QtCore import QObject, Signal

WAKE_WORD   = "hey jarvis"
MIC_DEVICE  = 4 # Varun's iPhone Microphone

class VoiceListener(QObject):
    wake_word_detected = Signal()
    command_received   = Signal(str)
    listening_changed  = Signal(bool)
    error              = Signal(str)

    def __init__(self):
        super().__init__()
        self._running    = False
        self._thread     = None
        self._recognizer = sr.Recognizer()
        self._recognizer.energy_threshold        = 300
        self._recognizer.dynamic_energy_threshold = True
        self._recognizer.pause_threshold         = 0.8

    def start(self):
        self._running = True
        self._thread  = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _loop(self):
        with sr.Microphone(device_index=MIC_DEVICE) as source:
            print("[Voice] Calibrating mic...")
            self._recognizer.adjust_for_ambient_noise(source, duration=1)
            print("[Voice] Ready — say 'Hey Jarvis'")
            while self._running:
                try:
                    self.listening_changed.emit(True)
                    audio = self._recognizer.listen(
                        source, timeout=5, phrase_time_limit=6
                    )
                    self.listening_changed.emit(False)

                    text = self._recognizer.recognize_google(audio).lower()
                    print(f"[Voice] Heard: '{text}'")
                    print(f"[Voice] Wake word check: '{WAKE_WORD}' in '{text}' = {WAKE_WORD in text}")

                    if WAKE_WORD in text:
                        print("[Voice] Wake word matched! Emitting signal...")
                        self.wake_word_detected.emit()
                        print("[Voice] Listening for command...")

                        self.listening_changed.emit(True)
                        audio2 = self._recognizer.listen(
                            source, timeout=6, phrase_time_limit=10
                        )
                        self.listening_changed.emit(False)

                        command = self._recognizer.recognize_google(audio2)
                        print(f"[Voice] Command: '{command}'")
                        self.command_received.emit(command)
                    else:
                        print("[Voice] Wake word not detected, listening again...")

                except sr.WaitTimeoutError:
                    self.listening_changed.emit(False)
                    print("[Voice] Timeout — no speech detected")
                except sr.UnknownValueError:
                    self.listening_changed.emit(False)
                    print("[Voice] Could not understand audio")
                except Exception as e:
                    self.listening_changed.emit(False)
                    self.error.emit(str(e))
                    print(f"[Voice] Error: {e}")