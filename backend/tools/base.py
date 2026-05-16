from typing import Dict, Any

class Tool:
    """Claude-Code style Tool base class"""
    def __init__(self, name: str, description: str, parameters: Dict[str, Any]):
        self.name = name
        self.description = description
        self.parameters = parameters

    def execute(self, **kwargs):
        raise NotImplementedError
