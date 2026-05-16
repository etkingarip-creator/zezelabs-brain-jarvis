import sounddevice as sd
import numpy as np
import speech_recognition as sr
import subprocess, threading, time, io, sys
import scipy.io.wavfile as wav
import pyttsx3

# ZOM v4 — Jarvis Voice Listener
# Mikrofon: Device 1 (Intel MME) — 16000Hz kabul etti, kanıtlandı çalışıyor
MIC_DEVICE   = 1
SAMPLE_RATE  = 16000
RECORD_SECS  = 4
WAKE_WORD    = "jarvis"

# ── TTS ──────────────────────────────────────────────────
engine = pyttsx3.init()
engine.setProperty('rate', 170)
engine.setProperty('volume', 0.9)
for v in engine.getProperty('voices'):
    if 'tr' in v.id.lower() or 'turkish' in (v.name or '').lower():
        engine.setProperty('voice', v.id)
        print(f"[TTS] Türkçe ses: {v.name}")
        break
else:
    print("[TTS] Türkçe ses yok, varsayılan kullanılıyor.")

def speak(text):
    print(f"[JARVIS] {text}")
    try: engine.say(text); engine.runAndWait()
    except: pass

# ── Komut işleme (ayrı thread — crash yok) ───────────────
def process_command(text):
    def _run():
        print(f"[ZOM] Komut: {text}")
        speak("Anlaşıldı, ZOM birimlerini harekete geçiriyorum.")
        try:
            cmd = ["docker","exec","-w","/openjarvis","zeze_jarvis_bridge",
                   "uv","run","python","-m","openjarvis.cli","skill","run",
                   "zom","--arg",f"task={text}"]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            out = r.stdout.strip() or r.stderr.strip()
            print(f"[ZOM] Yanıt: {out[:200]}")
        except subprocess.TimeoutExpired:
            speak("İşlem zaman aşımına uğradı.")
        except Exception as e:
            print(f"[ZOM] Hata: {e}")
    threading.Thread(target=_run, daemon=True).start()

# ── Ana döngü ─────────────────────────────────────────────
def main():
    r = sr.Recognizer()
    r.energy_threshold = 300
    r.dynamic_energy_threshold = True

    print("=" * 48)
    print("  ZOM v4 | Jarvis Voice Listener — AKTIF")
    print(f"  Cihaz: [{MIC_DEVICE}] {sd.query_devices(MIC_DEVICE)['name']}")
    print(f"  Wake word: '{WAKE_WORD}'")
    print("=" * 48)
    speak("Sistem hazır, sizi dinliyorum.")

    while True:
        try:
            print(".", end="", flush=True)
            rec = sd.rec(int(RECORD_SECS * SAMPLE_RATE),
                         samplerate=SAMPLE_RATE, channels=1,
                         dtype='int16', device=MIC_DEVICE)
            sd.wait()
            if np.abs(rec).max() < 60:
                continue
            buf = io.BytesIO()
            wav.write(buf, SAMPLE_RATE, rec)
            buf.seek(0)
            with sr.AudioFile(buf) as src:
                audio = r.record(src)
            text = r.recognize_google(audio, language="tr-TR").lower()
            if WAKE_WORD in text:
                cmd = text.split(WAKE_WORD, 1)[-1].strip()
                process_command(cmd) if cmd else speak("Efendim?")
        except sr.UnknownValueError:
            continue
        except sr.RequestError as e:
            print(f"\n[STT] API hatası: {e}"); time.sleep(2)
        except KeyboardInterrupt:
            print("\n[JARVIS] Kapatılıyor..."); speak("Göreve ara veriyorum."); sys.exit(0)
        except Exception as e:
            print(f"\n[ERR] {e}"); time.sleep(0.5)

if __name__ == "__main__":
    main()
