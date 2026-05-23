import os
import sys
import importlib
import logging

log = logging.getLogger("jarvis_plugins")

class PluginInterface:
    """Base class that all Jarvis plugins must inherit."""
    def __init__(self, name: str):
        self.name = name
        self.enabled = True
        
    def on_message(self, message: str) -> str:
        """Invoked when user sends a message, prior to sending to LLM.
        Allows prompt modifications or autonomous checks.
        """
        return message
        
    def on_response(self, response: str) -> str:
        """Invoked when LLM returns a response, prior to broadcasting.
        Allows response scrubbing or telemetry injection.
        """
        return response


class PluginManager:
    def __init__(self):
        self.plugins = []
        
    def register_plugin(self, plugin: PluginInterface):
        self.plugins.append(plugin)
        log.info(f"Plugin registered successfully: {plugin.name}")
        
    def execute_on_message(self, message: str) -> str:
        for plugin in self.plugins:
            if plugin.enabled:
                try:
                    message = plugin.on_message(message)
                except Exception as e:
                    log.error(f"Plugin {plugin.name} error on_message: {e}")
        return message
        
    def execute_on_response(self, response: str) -> str:
        for plugin in self.plugins:
            if plugin.enabled:
                try:
                    response = plugin.on_response(response)
                except Exception as e:
                    log.error(f"Plugin {plugin.name} error on_response: {e}")
        return response
