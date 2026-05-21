import json
import sys
import asyncio
import inspect
from typing import Dict, Any, Callable, Optional

class MCPServer:
    def __init__(self, tools: Optional[Dict[str, Callable]] = None):
        self.tools = tools or {}
    
    async def handle_request(self, req: Dict[str, Any]) -> Dict[str, Any]:
        method = req.get("method")
        params = req.get("params", {})
        
        if method == "tools/list":
            return {"result": list(self.tools.keys())}
        
        if method == "tools/call":
            tool_name = params.get("name")
            args = params.get("arguments", {})
            if tool_name in self.tools:
                fn = self.tools[tool_name]
                if inspect.iscoroutinefunction(fn):
                    result = await fn(**args)
                else:
                    res = fn(**args)
                    if inspect.isawaitable(res):
                        result = await res
                    else:
                        result = res
                return {"result": result}
            return {"error": {"code": -32601, "message": "Tool not found"}}
        
        return {"error": {"code": -32600, "message": "Invalid request"}}
    
    async def start_stdio(self):
        def read_line():
            return sys.stdin.readline()
        
        while True:
            line = await asyncio.to_thread(read_line)
            if not line:
                break
            try:
                req = json.loads(line)
                resp = await self.handle_request(req)
                if resp:
                    print(json.dumps(resp), flush=True)
            except json.JSONDecodeError:
                continue
