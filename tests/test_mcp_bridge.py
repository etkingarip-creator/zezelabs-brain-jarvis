import sys
import os
import subprocess
import asyncio
import pytest
from core.mcp.bridge import MCPServer
from core.mcp_client import MCPClient
from core.operator_runtime.clawde_kernel import ClawdeOperatorKernel
from core.operator_runtime.contracts import ToolRequest, RiskLevel

# 1. Test MCPServer listing tools
def test_mcp_server_lists_tools():
    async def mock_hello(name="world"):
        return f"hello {name}"
        
    server = MCPServer({"hello": mock_hello})
    
    async def run():
        req = {"method": "tools/list"}
        resp = await server.handle_request(req)
        assert resp["result"] == ["hello"]
        
        req_call = {"method": "tools/call", "params": {"name": "hello", "arguments": {"name": "test"}}}
        resp_call = await server.handle_request(req_call)
        assert resp_call["result"] == "hello test"
        
    asyncio.run(run())

# 2. Integration test with real subprocess using asyncio
def test_mcp_tool_invocation():
    async def run():
        workspace_root = os.path.abspath(os.getcwd())
        temp_file = os.path.join(workspace_root, "tests", "mcp_temp_test_server.py")
        
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(
                f"import sys\n"
                f"sys.path.insert(0, {repr(workspace_root)})\n"
                f"import asyncio\n"
                f"from core.mcp.bridge import MCPServer\n"
                f"async def mock_add(a, b):\n"
                f"    return a + b\n"
                f"server = MCPServer({{'add': mock_add}})\n"
                f"asyncio.run(server.start_stdio())\n"
            )
            
        # Use standard subprocess.Popen to bypass Windows SelectorEventLoop limitations in pytest
        proc = subprocess.Popen(
            [sys.executable, temp_file],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        class ThreadedProcessWrapper:
            def __init__(self, p):
                self.p = p
                self.stdin = self
                self.stdout = self
                
            def write(self, data):
                self.p.stdin.write(data)
                self.p.stdin.flush()
                
            async def drain(self):
                pass
                
            async def readline(self):
                def read():
                    return self.p.stdout.readline()
                return await asyncio.to_thread(read)
                
        wrapper = ThreadedProcessWrapper(proc)
        client = MCPClient(wrapper)
        try:
            tools = await client.list_tools()
            assert tools is not None
            assert "add" in tools["result"]
            
            res = await client.call_tool("add", {"a": 5, "b": 10})
            assert res is not None
            assert res["result"] == 15
        finally:
            proc.terminate()
            proc.wait()
            if os.path.exists(temp_file):
                os.remove(temp_file)
            
    asyncio.run(run())

# 3. Test security controls in ClawdeOperatorKernel
def test_execute_mcp_tool_success_and_denials():
    class FakeMCPClient:
        async def call_tool(self, name, arguments):
            return {"result": f"Executed {name} with {arguments}"}
            
    fake_client = FakeMCPClient()
    
    # 3.1 Test allowed tool
    kernel_app = ClawdeOperatorKernel(department="app_factory")
    req_allowed = ToolRequest(
        tool_name="file_read",
        action="read test file",
        args={"path": "hello.txt"}
    )
    res_allowed = asyncio.run(kernel_app.execute_mcp_tool(req_allowed, fake_client))
    assert res_allowed.success is True
    assert "Executed file_read" in res_allowed.stdout
    
    # 3.2 Test forbidden tool
    req_forbidden = ToolRequest(
        tool_name="git_push",
        action="push changes",
        args={}
    )
    res_forbidden = asyncio.run(kernel_app.execute_mcp_tool(req_forbidden, fake_client))
    assert res_forbidden.success is False
    assert "forbidden" in res_forbidden.error.lower()
    
    # 3.3 Test path traversal sanitization
    req_traversal = ToolRequest(
        tool_name="file_read",
        action="traverse up",
        args={"path": "../secret_file"}
    )
    res_traversal = asyncio.run(kernel_app.execute_mcp_tool(req_traversal, fake_client))
    assert res_traversal.success is False
    assert "path traversal" in res_traversal.error.lower()
    
    # 3.4 Test sensitive path sanitization
    req_sensitive = ToolRequest(
        tool_name="file_read",
        action="read .env",
        args={"path": "subfolder/.env.production"}
    )
    res_sensitive = asyncio.run(kernel_app.execute_mcp_tool(req_sensitive, fake_client))
    assert res_sensitive.success is False
    assert "protected file pattern" in res_sensitive.error.lower()
    
    # 3.5 Test dangerous command sanitization
    req_dangerous = ToolRequest(
        tool_name="file_read",
        action="run inject",
        args={"cmd": "some_cmd && rm -rf /"}
    )
    res_dangerous = asyncio.run(kernel_app.execute_mcp_tool(req_dangerous, fake_client))
    assert res_dangerous.success is False
    assert "blocklisted command pattern" in res_dangerous.error.lower()
