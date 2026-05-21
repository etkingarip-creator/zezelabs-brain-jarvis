import os
import json
import logging
from typing import Optional
from core.operator_runtime.policy_engine import PolicyEngine
from core.operator_runtime.clawde_kernel import ClawdeOperatorKernel

log = logging.getLogger("provider_sync")

class ProviderSyncOrchestrator:
    def __init__(self, deepseek_client=None, hermes_client=None, policy_engine=None, kernel=None):
        self.deepseek_client = deepseek_client
        self.hermes_client = hermes_client
        self.policy_engine = policy_engine or PolicyEngine()
        self.kernel = kernel or ClawdeOperatorKernel(department="jarvis")

    def get_mode(self) -> str:
        return os.getenv("ZOM_AI_MODE", "hybrid_deepseek_hermes").lower()

    def hermes_enabled(self) -> bool:
        return os.getenv("ZOM_ENABLE_HERMES_SYNC", "false").lower() == "true"

    def ollama_fallback_enabled(self) -> bool:
        return os.getenv("ZOM_ENABLE_OLLAMA_FALLBACK", "false").lower() == "true"

    def health_snapshot(self) -> dict:
        mode = self.get_mode()
        hermes_health = "unknown"
        if self.hermes_enabled():
            # Mock health check for Hermes since we are not making external requests in Phase 1 if not needed
            hermes_health = "offline" if not self.hermes_client else "online"
            
        return {
            "mode": mode,
            "hermes_enabled": self.hermes_enabled(),
            "hermes_status": hermes_health,
            "ollama_fallback_enabled": self.ollama_fallback_enabled(),
            "clawde_operator_enabled": os.getenv("ZOM_ENABLE_CLAWDE_OPERATOR", "true").lower() == "true"
        }

    async def plan_with_deepseek(self, prompt: str, metadata=None) -> dict:
        # Mocking deepseek plan
        log.info("DeepSeek planning started.")
        is_mock = os.getenv("ZOM_MOCK_DEEPSEEK", "false").lower() == "true"
        model = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
        
        return {
            "plan_status": "success",
            "provider": "deepseek" if not is_mock else f"mock_deepseek:{model}",
            "plan": {"action": "execute", "details": prompt}
        }

    async def execute_with_hermes(self, plan: dict, metadata=None) -> dict:
        if not self.hermes_enabled() or not self.hermes_client:
            return {
                "hermes_status": "offline",
                "degraded_mode": True,
                "recommendation": "enable Hermes or continue DeepSeek-only",
                "execution_status": "failed"
            }
        return {"execution_status": "success", "executor": "hermes"}

    async def execute_with_clawde(self, plan: dict, metadata=None) -> dict:
        from core.operator_runtime.clawde_kernel import ToolRequest
        
        action = plan.get("plan", {}).get("action", "unknown")
        details = plan.get("plan", {}).get("details", "")
        
        is_shell = "komut" in details or "bash" in details or "shell" in details
        if is_shell:
            req = ToolRequest(
                tool_name="shell_exec",
                action=details,
                args={"command": details}
            )
            result = self.kernel.execute_shell(req)
        else:
            req = ToolRequest(
                tool_name="file_edit",
                action=details,
                args={"path": "test.txt", "content": details}
            )
            result = self.kernel.edit_file(req)

        return {
            "execution_status": "success" if result.success else "failed",
            "executor": "clawde",
            "result": getattr(result, 'stdout', '') or getattr(result, 'error', '')
        }

    async def run_hybrid_task(self, prompt: str, metadata=None) -> dict:
        mode = self.get_mode()
        
        if mode == "deepseek_only":
            return await self.plan_with_deepseek(prompt, metadata)
        elif mode == "hermes_only":
            return await self.execute_with_hermes({"plan": {"action": "execute", "details": prompt}}, metadata)
        else: # hybrid_deepseek_hermes
            plan = await self.plan_with_deepseek(prompt, metadata)
            
            hermes_status = self.health_snapshot().get("hermes_status")
            if hermes_status == "offline" or not self.hermes_enabled():
                log.warning("Hermes is offline or disabled. Falling back to degraded DeepSeek-only mode.")
                plan["degraded_mode"] = True
                plan["hermes_status"] = "offline"
                plan["recommendation"] = "enable Hermes or continue DeepSeek-only"
                
                if os.getenv("ZOM_ENABLE_CLAWDE_OPERATOR", "true").lower() == "true":
                    clawde_res = await self.execute_with_clawde(plan, metadata)
                    plan["clawde_execution"] = clawde_res
                    
                return plan
                
            execution = await self.execute_with_hermes(plan, metadata)
            return {"plan": plan, "execution": execution}
