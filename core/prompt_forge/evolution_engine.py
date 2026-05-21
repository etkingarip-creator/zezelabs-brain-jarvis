import os
import logging
import httpx
from typing import Optional
from core.prompt_forge.auditor import FailureSignature
from core.prompt_forge.sandbox import SimulationStats
from core.ai.provider_sync import ProviderSyncOrchestrator

log = logging.getLogger("zom.prompt_forge.evolution_engine")

class EvolutionEngine:
    """
    Katman 3: Semantic Evolution Engine (The Reasoning Engine)
    Leverages DeepSeek's high reasoning capabilities to optimize system prompt templates
    based on live failure signatures and local sandbox stats.
    """
    def __init__(self, orchestrator: Optional[ProviderSyncOrchestrator] = None):
        self.orchestrator = orchestrator or ProviderSyncOrchestrator()

    async def evolve_prompt(self, current_prompt: str, failure_signature: FailureSignature, sandbox_stats: SimulationStats) -> str:
        """
        Evolves and optimizes the prompt template.
        """
        is_mock = os.getenv("ZOM_MOCK_DEEPSEEK", "false").lower() == "true"
        api_key = os.getenv("DEEPSEEK_API_KEY", "")
        
        system_instructions = (
            "You are the ZEZELABS Semantic Prompt Evolution Engine. "
            "Your task is to revise system prompts to prevent runtime errors (e.g., loops, path traversal) "
            "while fully preserving the agent's core capabilities. Output ONLY the updated prompt."
        )
        
        user_prompt = f"""
        Current Prompt Template:
        ---
        {current_prompt}
        ---
        
        We encountered a runtime failure:
        Error Type: {failure_signature.error_type}
        Signature: {failure_signature.signature}
        
        Local Sandbox Simulation Report:
        - Runs: {sandbox_stats.runs}
        - Successes: {sandbox_stats.successes}
        - Failures: {sandbox_stats.failures}
        - Success Rate: {sandbox_stats.success_rate * 100}%
        - Drift: {sandbox_stats.context_drift}
        - Recommendation: {sandbox_stats.recommendation}
        
        Instructions:
        1. Inject strict guardrails into the system prompt to explicitly prevent {failure_signature.error_type} ({failure_signature.signature}).
        2. Keep all core functionalities, tools, and formatting guidelines.
        3. Do not add any preamble, conversational text, or markdown code blocks around the prompt. Just output the final prompt.
        """

        if is_mock or not api_key or api_key == "test_key_do_not_commit":
            log.info("DeepSeek mock or offline. Performing autonomous semantic prompt modification...")
            return self._mock_evolve_prompt(current_prompt, failure_signature)

        try:
            base_url = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com").rstrip("/")
            model = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
            
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_instructions},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.2,
            }
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            
            async with httpx.AsyncClient(timeout=45) as client:
                resp = await client.post(f"{base_url}/chat/completions", headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                evolved_prompt = data["choices"][0]["message"]["content"].strip()
                if evolved_prompt:
                    return evolved_prompt
        except Exception as e:
            log.warning(f"Failed to evolve prompt using DeepSeek API: {e}. Falling back to autonomous mock update.")
            
        return self._mock_evolve_prompt(current_prompt, failure_signature)

    def _mock_evolve_prompt(self, current_prompt: str, failure_signature: FailureSignature) -> str:
        """
        Autonomous mock update that injects high-quality, real mitigation rules into the current prompt template.
        """
        mitigation_directives = ""
        
        if failure_signature.error_type == "path_traversal":
            mitigation_directives = (
                "\n\n# 🛡️ SECURITY GUARDRAILS (PATH TRAVERSAL PREVENTATIVE)\n"
                "- ABSOLUTE RULE: Never use path traversal or relative path links ('../', '..\\') to access paths outside workspace.\n"
                "- Always validate that target file paths are fully contained within the workspace root directory and do not traverse outside.\n"
                "- Do not attempt to access root-level, appData, or OS files unless explicitly requested and permitted."
            )
            
        elif failure_signature.error_type == "loop_detected":
            mitigation_directives = (
                "\n\n# 🔄 EXECUTION GUARDRAILS (ANTI-LOOP PREVENTATIVE)\n"
                "- ABSOLUTE RULE: Monitor tool execution for duplicate operations. Never repeat the exact same tool calls with the same arguments.\n"
                "- If a tool call fails, log the failure and select a different strategy instead of retrying infinitely.\n"
                "- Halt immediately and notify the system if a circular dependency or repetition is observed."
            )
            
        elif failure_signature.error_type == "execution_failed":
            mitigation_directives = (
                "\n\n# ⚙️ COMPONENT GUARDRAILS (ROBUST EXCEPTION HANDLING)\n"
                "- Always verify that system operations, commands, and file writes have succeeded before proceeding.\n"
                "- Catch and log all operational exceptions, wrapping execution in try-except-retry semantics gracefully."
            )
            
        else:
            mitigation_directives = (
                "\n\n# 🛡️ GENERAL GUARDRAILS (SYSTEM PREVENTATIVE)\n"
                "- Adhere to defensive programming and fail-safe defaults in all tool invocations and directory commands."
            )

        # Check if already present to prevent duplicate appending
        if mitigation_directives.strip() in current_prompt:
            return current_prompt
            
        return current_prompt.strip() + mitigation_directives
