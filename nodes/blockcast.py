"""Blockcast BEACON node health checker."""
import subprocess
from typing import Dict

class BlockcastHealth:
    def __init__(self, container_name='blockcast-beacon'):
        self.container_name = container_name
        self.network = 'Blockcast'

    def check(self) -> Dict:
        try:
            result = subprocess.run(
                f"docker inspect --format='{{{{.State.Status}}}}' {self.container_name}",
                shell=True, capture_output=True, text=True, timeout=10
            )
            status = result.stdout.strip().strip("'")
            if status == 'running':
                return {"network": self.network, "status": "healthy", "container": status}
            return {"network": self.network, "status": "unhealthy", "container": status}
        except Exception as e:
            return {"network": self.network, "status": "error", "error": str(e)}
