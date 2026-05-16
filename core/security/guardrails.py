import re
import logging

class Guardrails:
    """
    Security Layer inspired by Claude Code's Command Interception.
    Prevents destructive actions and limits file system access.
    """
    def __init__(self):
        self.logger = logging.getLogger("zom.security")
        
        # 1. FORBIDDEN COMMANDS (The "Never List")
        self.forbidden_patterns = [
            r"rm\s+-rf\s+/",            # Delete root
            r"mkfs",                    # Format disk
            r"drop\s+table",            # Database destruction
            r"truncate\s+table",
            r"chmod\s+-R\s+777",        # Insecure permissions
            r"chown\s+-R",
            r">\s+/dev/sda",            # Overwriting disk
            r"shutdown",                # System shutdown
            r"reboot",
            r":\(\)\{ :\|: &\};:",      # Fork bomb
        ]

    def validate_command(self, command: str) -> bool:
        """
        Returns True if the command is safe, False otherwise.
        """
        for pattern in self.forbidden_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                self.logger.error(f"🛑 SECURITY ALERT: Blocked dangerous command: {command}")
                return False
        
        # 2. PATH VALIDATION (Simplified)
        # Prevent accessing paths outside the workspace
        if ".." in command and ("/" in command or "\\" in command):
            if not self._is_path_safe(command):
                self.logger.error(f"🛑 SECURITY ALERT: Blocked unauthorized path access: {command}")
                return False

        return True

    def _is_path_safe(self, command: str) -> bool:
        # Placeholder for complex path validation logic
        # For now, we block any attempt to go too many levels up
        if command.count("..") > 3: return False
        return True

    def sanitize_output(self, output: str) -> str:
        """
        Filters out sensitive info (API keys, passwords) from command outputs.
        """
        # Mask GEMINI_API_KEY etc.
        sanitized = re.sub(r"AIza[0-9A-Za-z-_]{35}", "[MASKED_API_KEY]", output)
        return sanitized
