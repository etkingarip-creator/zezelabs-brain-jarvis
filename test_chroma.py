import chromadb
import os

host = os.getenv("CHROMA_HOST", "chromadb")
port = int(os.getenv("CHROMA_PORT", 8000))

print(f"Connecting to Chroma at {host}:{port}...")
try:
    from chromadb.config import Settings
    client = chromadb.HttpClient(
        host=host, 
        port=port,
        settings=Settings(
            chroma_api_impl="chromadb.api.fastapi.FastAPI",
            chroma_server_host=host,
            chroma_server_http_port=port
        )
    )
    print("Heartbeat:", client.heartbeat())
    print("Collections:", client.list_collections())
except Exception as e:
    print("Error:", e)
