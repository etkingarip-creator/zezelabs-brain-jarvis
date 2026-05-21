import pytest
from desktop.backend_launcher import BackendLauncher

def test_desktop_launcher_build_command():
    launcher = BackendLauncher()
    cmd = launcher.build_command()
    assert isinstance(cmd, list)
    assert "uvicorn" in cmd
    assert "backend.jarvis:app" in cmd
    
def test_desktop_launcher_safe_env():
    # Only asserting it doesn't crash on import/init
    launcher = BackendLauncher()
    assert launcher.host == "127.0.0.1"
    assert launcher.port == "8000"
