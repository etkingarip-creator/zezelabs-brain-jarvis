import httpx
import asyncio
import os
import sys

async def check_ollama():
    url = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
    print(f"--- ZOM Beyin Kontrolü (Ollama) ---")
    print(f"URL: {url}")
    
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            # 1. Baglanti Kontrolu
            resp = await client.get(f"{url}/api/tags")
            if resp.status_code == 200:
                print("✅ [BAŞARILI] Ollama sunucusuna bağlanıldı.")
                models = resp.json().get("models", [])
                if models:
                    print(f"✅ [BAŞARILI] Yüklü modeller bulundu:")
                    for m in models:
                        print(f"  - {m['name']} ({m.get('details', {}).get('parameter_size', 'N/A')})")
                    
                    # Phi3 kontrolu
                    phi3_exists = any(m['name'].startswith('phi3') for m in models)
                    if not phi3_exists:
                        print("\n⚠️ [UYARI] 'phi3' modeli bulunamadı. Jarvis en iyi bu modelle çalışır.")
                        print("İndirmek için şu komutu kullanabilirsin: 'ollama pull phi3'")
                else:
                    print("\n❌ [HATA] Hiç model yüklü değil. Jarvis çalışamaz.")
                    print("Lütfen bir model indirin: 'ollama pull phi3'")
            else:
                print(f"\n❌ [HATA] Ollama hata döndürdü: {resp.status_code}")
    except Exception as e:
        print(f"\n❌ [HATA] Ollama'ya bağlanılamadı. Sunucu çalışıyor mu?")
        print(f"Hata detayı: {e}")
        print("\nÇözüm adımları:")
        print("1. Ollama uygulamasının açık olduğundan emin olun.")
        print(f"2. {url} adresine tarayıcıdan erişebiliyor musunuz kontrol edin.")
        print("3. Güvenlik duvarının portu engellemediğinden emin olun.")

if __name__ == "__main__":
    asyncio.run(check_ollama())
