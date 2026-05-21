import json
import asyncio
from typing import Dict, Any

class MCPClient:
    def __init__(self, process):
        self.process = process
    
    async def _send(self, method: str, params: Dict[str, Any] = None):
        req = json.dumps({"method": method, "params": params or {}})
        payload = req + "\n"
        try:
            self.process.stdin.write(payload.encode("utf-8"))
        except TypeError:
            self.process.stdin.write(payload)
        await self.process.stdin.drain()
        
        resp_line = await self.process.stdout.readline()
        if not resp_line:
            return None
        if isinstance(resp_line, bytes):
            resp_line = resp_line.decode("utf-8")
        return json.loads(resp_line)
    
    async def list_tools(self):
        return await self._send("tools/list")
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]):
        return await self._send("tools/call", {"name": name, "arguments": arguments})
