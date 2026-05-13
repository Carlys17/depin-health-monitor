#!/usr/bin/env python3
"""DePIN Health Monitor - Multi-network node health checker."""

import subprocess
import json
import time
import sys
from datetime import datetime
from typing import Dict, List, Optional

class NodeHealth:
    def __init__(self, name: str, network: str, check_cmd: str):
        self.name = name
        self.network = network
        self.check_cmd = check_cmd
        self.last_check = None
        self.status = "unknown"
        self.details = {}

    def check(self) -> Dict:
        """Run health check and return status."""
        try:
            result = subprocess.run(
                self.check_cmd, shell=True, capture_output=True, text=True, timeout=30
            )
            self.status = "healthy" if result.returncode == 0 else "unhealthy"
            self.details = {
                "stdout": result.stdout[:500],
                "stderr": result.stderr[:200],
                "exit_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            self.status = "timeout"
            self.details = {"error": "Check timed out after 30s"}
        except Exception as e:
            self.status = "error"
            self.details = {"error": str(e)}
        
        self.last_check = datetime.utcnow().isoformat()
        return self.to_dict()

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "network": self.network,
            "status": self.status,
            "last_check": self.last_check,
            "details": self.details
        }

class DockerHealth(NodeHealth):
    """Health check for Docker-based nodes."""
    
    def check(self) -> Dict:
        try:
            result = subprocess.run(
                f"docker inspect --format='{{{{.State.Status}}}}' {self.name}",
                shell=True, capture_output=True, text=True, timeout=10
            )
            container_status = result.stdout.strip().strip("'")
            
            if container_status == "running":
                # Check logs for errors
                log_result = subprocess.run(
                    f"docker logs --tail 20 {self.name} 2>&1 | grep -i 'error\\|fail\\|panic' | wc -l",
                    shell=True, capture_output=True, text=True, timeout=10
                )
                error_count = int(log_result.stdout.strip())
                self.status = "healthy" if error_count == 0 else "degraded"
                self.details = {
                    "container_status": container_status,
                    "recent_errors": error_count
                }
            else:
                self.status = "unhealthy"
                self.details = {"container_status": container_status}
        except Exception as e:
            self.status = "error"
            self.details = {"error": str(e)}
        
        self.last_check = datetime.utcnow().isoformat()
        return self.to_dict()

class SystemdHealth(NodeHealth):
    """Health check for systemd service nodes."""
    
    def check(self) -> Dict:
        try:
            result = subprocess.run(
                f"systemctl is-active {self.name}",
                shell=True, capture_output=True, text=True, timeout=10
            )
            service_status = result.stdout.strip()
            self.status = "healthy" if service_status == "active" else "unhealthy"
            
            # Get uptime
            uptime_result = subprocess.run(
                f"systemctl show {self.name} --property=ActiveEnterTimestamp",
                shell=True, capture_output=True, text=True, timeout=10
            )
            self.details = {
                "service_status": service_status,
                "since": uptime_result.stdout.strip().split("=", 1)[-1]
            }
        except Exception as e:
            self.status = "error"
            self.details = {"error": str(e)}
        
        self.last_check = datetime.utcnow().isoformat()
        return self.to_dict()

def get_default_nodes() -> List[NodeHealth]:
    """Return default DePIN nodes to monitor."""
    return [
        DockerHealth("tashi-depin-worker", "Tashi", "docker ps | grep tashi"),
        SystemdHealth("dragonball-hunter.service", "DragonBall", "systemctl is-active dragonball-hunter"),
    ]

def check_all(nodes: Optional[List[NodeHealth]] = None) -> List[Dict]:
    """Check all nodes and return results."""
    if nodes is None:
        nodes = get_default_nodes()
    
    results = []
    for node in nodes:
        result = node.check()
        results.append(result)
        status_icon = {"healthy": "✅", "degraded": "⚠️", "unhealthy": "🔴", "error": "❌", "timeout": "⏰"}.get(result["status"], "❓")
        print(f"{status_icon} {result['name']} ({result['network']}): {result['status']}")
    
    return results

def generate_report(results: List[Dict]) -> str:
    """Generate markdown report."""
    healthy = sum(1 for r in results if r["status"] == "healthy")
    total = len(results)
    
    report = f"# DePIN Health Report\n"
    report += f"**Time:** {datetime.utcnow().isoformat()}Z\n"
    report += f"**Status:** {healthy}/{total} healthy\n\n"
    
    for r in results:
        icon = {"healthy": "✅", "degraded": "⚠️", "unhealthy": "🔴"}.get(r["status"], "❌")
        report += f"{icon} **{r['name']}** ({r['network']}): {r['status']}\n"
    
    return report

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="DePIN Health Monitor")
    parser.add_argument("--check-all", action="store_true", help="Check all nodes")
    parser.add_argument("--report", action="store_true", help="Generate report")
    args = parser.parse_args()
    
    if args.check_all or args.report:
        results = check_all()
        if args.report:
            print("\n" + generate_report(results))
    else:
        parser.print_help()
