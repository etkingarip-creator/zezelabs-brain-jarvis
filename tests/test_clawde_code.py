import pytest
import asyncio
from core.operator_runtime.clawde_kernel import ClawdeOperatorKernel

def test_execute_code_success():
    kernel = ClawdeOperatorKernel()
    
    async def run():
        result = await kernel.execute_code("print('hello')")
        assert result["success"] is True
        assert "hello" in result["output"]
        
    asyncio.run(run())

def test_execute_code_timeout():
    kernel = ClawdeOperatorKernel()
    
    async def run():
        result = await kernel.execute_code("while True: pass", timeout=1)
        assert result["success"] is False
        assert "timeout" in result["error"]
        
    asyncio.run(run())

def test_execute_code_security():
    kernel = ClawdeOperatorKernel()
    
    async def run():
        result = await kernel.execute_code("import os")
        assert result["success"] is False
        assert "forbidden" in result["error"].lower()
        
    asyncio.run(run())
