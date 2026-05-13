"""OptimAI Network node health checker."""
import subprocess
from typing import Dict

class OptimAIHealth:
    def __init__(self):
        self.network = 'OptimAI'

    def check(self) -> Dict:
        try:
            result = subprocess.run(
                'systemctl is-active optimai-node 2>/dev/null || echo inactive',
                shell=True, capture_output=True, text=True, timeout=10
            )
            status = result.stdout.strip()
            return {"network": self.network, "status": "healthy" if status == "active" else "unhealthy", "service": status}
        except Exception as e:
            return {"network": self.network, "status": "error", "error": str(e)}
