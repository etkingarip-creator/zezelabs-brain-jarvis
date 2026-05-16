from flask import Flask, request, jsonify
import subprocess
import json
import os
import sys

app = Flask(__name__)

# Config
OPENJARVIS_ROOT = os.getenv("OPENJARVIS_ROOT", "C:/Users/Zezelabs2/OpenJarvis")

@app.route('/query', methods=['POST'])
def query_jarvis():
    """
    ZOM ajanlarından gelen istemleri alır ve OpenJarvis CLI üzerinden Jarvis'in beynine iletir.
    """
    try:
        data = request.json
        prompt = data.get("prompt", "")
        model = data.get("model", "default")
        
        print(f"[JarvisBridge] 🧠 İstek alındı (Model: {model})")
        
        # OpenJarvis CLI'yı uv üzerinden çalıştır
        # 'query' komutu Jarvis'in ana LLM motorunu tetikler
        result = subprocess.run(
            ["uv", "run", "python", "-m", "openjarvis.cli", "query", prompt],
            cwd=OPENJARVIS_ROOT,
            capture_output=True, text=True, timeout=60
        )
        
        if result.returncode != 0:
            return jsonify({
                "response": f"Jarvis Hatası: {result.stderr}",
                "status": "error"
            }), 500
            
        output = result.stdout.strip()
        print(f"[JarvisBridge] ✅ Jarvis'ten cevap alındı.")
        
        return jsonify({
            "response": output,
            "status": "success"
        })
        
    except Exception as e:
        return jsonify({
            "response": f"Köprü Sunucusu Hatası: {str(e)}",
            "status": "error"
        }), 500

if __name__ == "__main__":
    # Docker konteyner içinden erişilebilir olması için 0.0.0.0:7000'de başlat
    app.run(host='0.0.0.0', port=7000)
