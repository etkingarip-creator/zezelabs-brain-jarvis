import asyncio
from typing import Optional, Dict

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    _MCP_AVAILABLE = True
except ImportError:
    _MCP_AVAILABLE = False

class MCPClientManager:
    """
    ZOM v4 MCP (Model Context Protocol) Baglanti Yoneticisi.
    Ajanlarin dis dunyadaki MCP sunuculariyla (SQLite, GitHub vs.) konusmasini saglar.
    """
    def __init__(self):
        self.active_servers = {}
        if not _MCP_AVAILABLE:
            print("[MCP] ⚠️ 'mcp' kutuphanesi bulunamadi. MCP baglantilari calismayacak.")

    async def _connect_and_list_tools(self, command: str, args: list) -> list:
        if not _MCP_AVAILABLE:
            return []
            
        server_params = StdioServerParameters(command=command, args=args, env=None)
        
        try:
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools_result = await session.list_tools()
                    return [
                        {"name": t.name, "description": t.description, "inputSchema": t.inputSchema}
                        for t in tools_result.tools
                    ]
        except Exception as e:
            print(f"[MCP] ⚠️ Baglanti hatasi ({command}): {e}")
            return []

    def get_server_tools_sync(self, command: str, args: list) -> list:
        """
        Senkron (blocking) ajan thread'leri icin async MCP istemcisini calistirir.
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        return loop.run_until_complete(self._connect_and_list_tools(command, args))
