import httpx
import json

def test_brain():
    url = "http://127.0.0.1:11434/api/generate"
    payload = {
        "model": "phi3:latest",
        "prompt": "merhaba, sistemlerin calisiyor mu? kisa cevap ver.",
        "stream": False
    }
    try:
        print("Beyin testi baslatiliyor...")
        response = httpx.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            result = response.json().get("response", "")
            print(f"BEYİN AKTİF! Jarvis Cevabi: {result}")
        else:
            print(f"HATA: Ollama cevap verdi ama durum kodu {response.status_code}")
    except Exception as e:
        print(f"BEYİN ÇALIŞMIYOR: {e}")

if __name__ == "__main__":
    test_brain()
