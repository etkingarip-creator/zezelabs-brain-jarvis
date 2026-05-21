import pytest
import os
import asyncio
import httpx
from unittest.mock import AsyncMock, MagicMock, patch
from core.ai.provider_sync import ProviderSyncOrchestrator

def test_hermes_sync_disabled():
    """Verify Hermes status synchronizer handles disabled mode natively"""
    with patch.dict(os.environ, {"ZOM_ENABLE_HERMES_SYNC": "false"}):
        orchestrator = ProviderSyncOrchestrator()
        assert orchestrator.hermes_enabled() is False
        
        # Test health snapshot
        snapshot = orchestrator.health_snapshot()
        assert snapshot["hermes_enabled"] is False
        assert snapshot["hermes_status"] == "unknown"
        
        # Test status sync
        res = asyncio.run(orchestrator.sync_hermes_status())
        assert res["status"] == "disabled"

def test_hermes_sync_success():
    """Mock-simulate a successful connection to the Hermes status endpoint"""
    async def run_test():
        with patch.dict(os.environ, {
            "ZOM_ENABLE_HERMES_SYNC": "true",
            "HERMES_API_URL": "https://api.mockhermes.ai",
            "HERMES_API_KEY": "test-key"
        }):
            orchestrator = ProviderSyncOrchestrator()
            assert orchestrator.hermes_enabled() is True
            
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "online", "sync_count": 42}
            
            # Mock httpx.AsyncClient.get
            with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
                mock_get.return_value = mock_response
                
                res = await orchestrator.sync_hermes_status()
                assert res["status"] == "online"
                assert res["sync_count"] == 42
                
                # Verify authorization header is passed
                mock_get.assert_called_once()
                args, kwargs = mock_get.call_args
                assert "Authorization" in kwargs["headers"]
                assert kwargs["headers"]["Authorization"] == "Bearer test-key"
                
    asyncio.run(run_test())

def test_hermes_sync_offline_and_error():
    """Mock-simulate a degraded or offline API response"""
    async def run_test():
        with patch.dict(os.environ, {
            "ZOM_ENABLE_HERMES_SYNC": "true",
            "HERMES_API_URL": "https://api.mockhermes.ai"
        }):
            orchestrator = ProviderSyncOrchestrator()
            
            # 1. Connection error / Request error
            with patch("httpx.AsyncClient.get", side_effect=httpx.RequestError("Connection timeout")):
                res = await orchestrator.sync_hermes_status()
                assert res["status"] == "offline"
                assert "error" in res
                
            # 2. HTTP 500 Server Error
            mock_response = MagicMock()
            mock_response.status_code = 500
            with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
                mock_get.return_value = mock_response
                res = await orchestrator.sync_hermes_status()
                assert res["status"] == "error"
                assert res["code"] == 500
                
    asyncio.run(run_test())
