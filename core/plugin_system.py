"""
╔══════════════════════════════════════════════════════════╗
║  ZEZELABS JARVIS — Plugin Sistemi v2.0                   ║
║  Dinamik plugin yükleme, yaşam döngüsü yönetimi         ║
╚══════════════════════════════════════════════════════════╝
"""
import os
import sys
import importlib
import importlib.util
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

log = logging.getLogger("jarvis.plugins")


# ═══════════════════════════════════════════════════════════
# BASE PLUGIN INTERFACE
# ═══════════════════════════════════════════════════════════
class PluginInterface:
    """
    Tüm Jarvis pluginlerinin miras alması gereken temel sınıf.
    
    Örnek kullanım:
        class MyPlugin(PluginInterface):
            def __init__(self):
                super().__init__("my_plugin")
            def on_message(self, message: str) -> str:
                return message.upper()
    """
    def __init__(self, name: str, version: str = "1.0.0", description: str = ""):
        self.name = name
        self.version = version
        self.description = description
        self.enabled = True
        self.metadata: Dict[str, Any] = {}

    def on_load(self) -> None:
        """Plugin yüklendiğinde çağrılır."""
        pass

    def on_unload(self) -> None:
        """Plugin kaldırıldığında çağrılır."""
        pass

    def on_message(self, message: str) -> str:
        """Kullanıcı mesajı LLM'e gitmeden önce işlenir."""
        return message

    def on_response(self, response: str) -> str:
        """LLM cevabı kullanıcıya gelmeden önce işlenir."""
        return response

    def on_department_event(self, dept_id: str, event: str) -> None:
        """Departman olaylarına hook (ör. seçim, görev tamamlama)."""
        pass

    def __repr__(self) -> str:
        status = "✅" if self.enabled else "❌"
        return f"{status} Plugin({self.name} v{self.version})"


# ═══════════════════════════════════════════════════════════
# PLUGIN MANAGER
# ═══════════════════════════════════════════════════════════
class PluginManager:
    """
    Plugin yaşam döngüsünü, dinamik yüklemeyi ve
    pipeline çalıştırmayı yönetir.
    """
    def __init__(self):
        self.plugins: List[PluginInterface] = []
        self._registry: Dict[str, PluginInterface] = {}

    # ── Kayıt ────────────────────────────────────────────
    def register(self, plugin: PluginInterface) -> None:
        """Bir plugin örneğini manuel olarak kaydet."""
        if plugin.name in self._registry:
            log.warning(f"Plugin '{plugin.name}' zaten kayıtlı, üzerine yazılıyor.")
        plugin.on_load()
        self.plugins.append(plugin)
        self._registry[plugin.name] = plugin
        log.info(f"Plugin kayıtlandı: {plugin}")

    def unregister(self, name: str) -> bool:
        """İsme göre plugin kaldır."""
        plugin = self._registry.pop(name, None)
        if plugin:
            plugin.on_unload()
            self.plugins = [p for p in self.plugins if p.name != name]
            log.info(f"Plugin kaldırıldı: {name}")
            return True
        return False

    def get(self, name: str) -> Optional[PluginInterface]:
        return self._registry.get(name)

    def enable(self, name: str) -> None:
        if name in self._registry:
            self._registry[name].enabled = True

    def disable(self, name: str) -> None:
        if name in self._registry:
            self._registry[name].enabled = False

    # ── Dinamik Yükleme ──────────────────────────────────
    def load_from_directory(self, directory: str) -> int:
        """
        Bir klasördeki tüm plugin dosyalarını (plugin_*.py) dinamik olarak yükler.
        Yüklenen plugin sayısını döner.
        """
        count = 0
        plugin_dir = Path(directory)
        if not plugin_dir.exists():
            log.warning(f"Plugin klasörü bulunamadı: {directory}")
            return 0

        for py_file in sorted(plugin_dir.glob("plugin_*.py")):
            try:
                spec = importlib.util.spec_from_file_location(py_file.stem, py_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    # Modüldeki tüm PluginInterface alt sınıflarını bul
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (isinstance(attr, type)
                                and issubclass(attr, PluginInterface)
                                and attr is not PluginInterface):
                            instance = attr()
                            self.register(instance)
                            count += 1
            except Exception as e:
                log.error(f"Plugin yükleme hatası ({py_file.name}): {e}")

        log.info(f"Toplam {count} plugin yüklendi: {directory}")
        return count

    # ── Pipeline Çalıştırma ───────────────────────────────
    def process_message(self, message: str) -> str:
        """Aktif tüm pluginlerin on_message pipeline'ını çalıştır."""
        for plugin in self.plugins:
            if plugin.enabled:
                try:
                    message = plugin.on_message(message)
                except Exception as e:
                    log.error(f"[{plugin.name}] on_message hatası: {e}")
        return message

    def process_response(self, response: str) -> str:
        """Aktif tüm pluginlerin on_response pipeline'ını çalıştır."""
        for plugin in self.plugins:
            if plugin.enabled:
                try:
                    response = plugin.on_response(response)
                except Exception as e:
                    log.error(f"[{plugin.name}] on_response hatası: {e}")
        return response

    def fire_department_event(self, dept_id: str, event: str) -> None:
        """Tüm pluginlere departman olayı bildir."""
        for plugin in self.plugins:
            if plugin.enabled:
                try:
                    plugin.on_department_event(dept_id, event)
                except Exception as e:
                    log.error(f"[{plugin.name}] department_event hatası: {e}")

    # ── Durum ────────────────────────────────────────────
    def status(self) -> List[Dict[str, Any]]:
        """Tüm pluginlerin durum bilgisini döner."""
        return [
            {
                "name": p.name,
                "version": p.version,
                "description": p.description,
                "enabled": p.enabled,
            }
            for p in self.plugins
        ]

    def __len__(self) -> int:
        return len(self.plugins)

    def __repr__(self) -> str:
        return f"PluginManager({len(self.plugins)} plugins)"


# ═══════════════════════════════════════════════════════════
# BUILT-IN EXAMPLE PLUGINS
# ═══════════════════════════════════════════════════════════
class LoggingPlugin(PluginInterface):
    """Tüm mesaj ve cevapları loglar."""
    def __init__(self):
        super().__init__("logging_plugin", "1.0.0", "Mesaj ve cevap loglama")
        self._log = logging.getLogger("jarvis.plugin.logging")

    def on_message(self, message: str) -> str:
        self._log.debug(f"[MSG→LLM] {message[:120]}")
        return message

    def on_response(self, response: str) -> str:
        self._log.debug(f"[LLM→USR] {response[:120]}")
        return response


class SafetyPlugin(PluginInterface):
    """Temel güvenlik filtresi."""
    _BLOCKED = ["rm -rf", "format c:", "del /f /s"]

    def __init__(self):
        super().__init__("safety_plugin", "1.0.0", "Zararlı komut filtresi")

    def on_message(self, message: str) -> str:
        msg_lower = message.lower()
        for blocked in self._BLOCKED:
            if blocked in msg_lower:
                log.warning(f"SafetyPlugin: engellenen ifade tespit edildi: '{blocked}'")
                return "[GÜVENLİK] Bu komut JARVIS tarafından engellendi."
        return message


class TelemetryPlugin(PluginInterface):
    """Mesaj istatistiklerini takip eder."""
    def __init__(self):
        super().__init__("telemetry_plugin", "1.0.0", "Kullanım istatistikleri")
        self.message_count = 0
        self.response_count = 0
        self.total_chars_in = 0
        self.total_chars_out = 0

    def on_message(self, message: str) -> str:
        self.message_count += 1
        self.total_chars_in += len(message)
        return message

    def on_response(self, response: str) -> str:
        self.response_count += 1
        self.total_chars_out += len(response)
        return response

    def get_stats(self) -> Dict[str, int]:
        return {
            "messages": self.message_count,
            "responses": self.response_count,
            "chars_in": self.total_chars_in,
            "chars_out": self.total_chars_out,
        }


# ═══════════════════════════════════════════════════════════
# GLOBAL SINGLETON
# ═══════════════════════════════════════════════════════════
_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """Uygulama genelinde tek bir PluginManager örneği döner."""
    global _manager
    if _manager is None:
        _manager = PluginManager()
        # Built-in pluginleri kaydet
        _manager.register(LoggingPlugin())
        _manager.register(SafetyPlugin())
        _manager.register(TelemetryPlugin())
        log.info("PluginManager başlatıldı (built-in pluginler yüklendi)")
    return _manager
