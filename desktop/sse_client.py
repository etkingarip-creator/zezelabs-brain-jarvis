import sseclient
import threading
import time

class SSELogClient:
    def __init__(self, url="http://127.0.0.1:8000/api/runtime/streamlogs"):
        self.url = url
        self.running = False
        self.thread = None
    
    def start(self, callback):
        self.running = True
        self.thread = threading.Thread(target=self._listen, args=(callback,))
        self.thread.daemon = True
        self.thread.start()
    
    def _listen(self, callback):
        import urllib.request
        while self.running:
            try:
                req = urllib.request.Request(self.url)
                with urllib.request.urlopen(req, timeout=30) as r:
                    import sseclient
                    client = sseclient.SSEClient(r)
                    for event in client.events():
                        if not self.running:
                            break
                        callback(event.data)
            except Exception:
                time.sleep(2.0)
                if not self.running:
                    break
    
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
