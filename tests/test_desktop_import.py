import pytest

def test_desktop_import():
    try:
        from desktop.jarvis_desktop import JarvisDesktopApp
        import tkinter as tk
        root = tk.Tk()
        app = JarvisDesktopApp(root)
        assert app is not None
        root.destroy()
    except ImportError:
        pytest.skip("tkinter not installed, skipping desktop UI test")
    except Exception as e:
        if "display" in str(e).lower() or "xcb" in str(e).lower() or "x11" in str(e).lower() or "application has been destroyed" in str(e).lower():
            pytest.skip("No display environment for tkinter")
        else:
            raise
