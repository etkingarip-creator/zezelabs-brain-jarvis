import pytest

@pytest.mark.anyio
async def test_execute_code_success():
    from core.operator_runtime.clawde_kernel import ClawdeOperatorKernel
    kernel = ClawdeOperatorKernel()
    result = await kernel.execute_code("print('hello')")
    assert result["success"] is True
    assert "hello" in result["output"]

@pytest.mark.anyio
async def test_execute_code_timeout():
    from core.operator_runtime.clawde_kernel import ClawdeOperatorKernel
    kernel = ClawdeOperatorKernel()
    result = await kernel.execute_code("while True: pass", timeout=1)
    assert result["success"] is False
    assert "timeout" in result["error"]

@pytest.mark.anyio
async def test_execute_code_security():
    from core.operator_runtime.clawde_kernel import ClawdeOperatorKernel
    kernel = ClawdeOperatorKernel()
    result = await kernel.execute_code("import os")
    assert result["success"] is False
    assert "forbidden" in result["error"].lower()
