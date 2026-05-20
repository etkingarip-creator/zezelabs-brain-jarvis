import os
import sys
import json
import logging

class QueryEngine:
    """
    Advanced Query Engine - Claude Code Protocol (Final Stabilized v7.6)
    Injects Anthropic's autonomous reasoning directly into Zezelabs Jarvis.
    """
    def __init__(self, model_name=None):
        import os
        self.model_name = model_name or os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
        self.max_turns = 10
        self.history = []

    def get_system_prompt(self):
        import os
        root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        
        return f"""<primary_directive>
You are JARVIS (ZOM Orchestrator). 
You operate under the CLAUDE CODE PROTOCOL.
Project Root: {root_path}

## THINKING PROCESS (MANDATORY):
1. <thinking>: Analyze user intent, break down tasks, and plan tool usage.
2. <tool_use>: Call tools sequentially based on the plan.
3. Observe: Evaluate tool results and refine the plan in the next <thinking> block.

## MISSION:
Coordinate all zeze_* agents. If a directory is missing, use 'BashTool' to explore.
</primary_directive>"""

    async def run_turn(self, user_input, connection_manager):
        # Implementation of the thinking loop logic
        # This will be called by the main jarvis.py bridge
        pass
