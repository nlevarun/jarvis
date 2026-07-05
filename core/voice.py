import threading
import time
import speech_recognition as sr
from PySide6.QtCore import QObject, Signal

WAKE_WORD       = "hey jarvis"
MIC_DEVICE      = 2
SESSION_TIMEOUT = 30


class VoiceListener(QObject):
    wake_word_detected = Signal()
    command_received   = Signal(str)
    listening_changed  = Signal(bool)
    session_started    = Signal()
    session_ended      = Signal()
    error              = Signal(str)

    def __init__(self):
        super().__init__()
        self._running      = False
        self._thread       = None
        self._session      = False
        self._last_command = 0
        self._recognizer   = sr.Recognizer()
        self._recognizer.energy_threshold          = 300
        self._recognizer.dynamic_energy_threshold  = True

    def start(self):
        self._running = True
        self._thread  = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _open_session(self):
        self._session      = True
        self._last_command = time.time()
        self.session_started.emit()
        print("[Voice] Session opened — listening continuously")

    def _close_session(self):
        self._session = False
        self.session_ended.emit()
        print("[Voice] Session closed — say 'Hey Jarvis' to reactivate")

    def _loop(self):
        with sr.Microphone(device_index=MIC_DEVICE) as source:
            print("[Voice] Calibrating mic...")
            self._recognizer.adjust_for_ambient_noise(source, duration=1)
            self._recognizer.pause_threshold       = 1.2
            self._recognizer.phrase_threshold      = 0.3
            self._recognizer.non_speaking_duration = 1.0
            print("[Voice] Ready — say 'Hey Jarvis'")

            while self._running:
                try:
                    if self._session:
                        elapsed = time.time() - self._last_command
                        if elapsed > SESSION_TIMEOUT:
                            self._close_session()

                    self.listening_changed.emit(True)
                    timeout = 5 if not self._session else 10

                    audio = self._recognizer.listen(
                        source,
                        timeout=timeout,
                        phrase_time_limit=15
                    )
                    self.listening_changed.emit(False)
                    time.sleep(0.3)

                    text = self._recognizer.recognize_google(audio).lower()
                    print(f"[Voice] Heard: '{text}'")

                    if not self._session:
                        if WAKE_WORD in text:
                            print("[Voice] Wake word detected!")
                            self.wake_word_detected.emit()
                            self._open_session()
                            command = text.replace(WAKE_WORD, "").strip()
                            if len(command) > 3:
                                print(f"[Voice] Inline command: '{command}'")
                                self._last_command = time.time()
                                self.command_received.emit(command)
                    else:
                        if WAKE_WORD in text:
                            command = text.replace(WAKE_WORD, "").strip()
                            self._last_command = time.time()
                            if len(command) > 3:
                                print(f"[Voice] Command: '{command}'")
                                self.command_received.emit(command)
                            else:
                                print("[Voice] Session refreshed")
                        elif len(text.strip()) > 2:
                            print(f"[Voice] Command: '{text}'")
                            self._last_command = time.time()
                            self.command_received.emit(text)

                except sr.WaitTimeoutError:
                    self.listening_changed.emit(False)
                    if self._session:
                        elapsed = time.time() - self._last_command
                        remaining = int(SESSION_TIMEOUT - elapsed)
                        if remaining > 0:
                            print(f"[Voice] Session active — {remaining}s until timeout")
                        else:
                            self._close_session()
                except sr.UnknownValueError:
                    self.listening_changed.emit(False)
                except Exception as e:
                    self.listening_changed.emit(False)
                    self.error.emit(str(e))
                    print(f"[Voice] Error: {e}")