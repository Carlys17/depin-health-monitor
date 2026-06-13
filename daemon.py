"""Daemon loop: poll all configured nodes, alert on transitions, write a JSON snapshot."""
from __future__ import annotations
import argparse
import json
import os
import sys
import time
from pathlib import Path

import yaml
from alerter import TelegramAlerter, WebhookAlerter
from monitor import (
    NodeHealth, DockerHealth, SystemdHealth,
    check_all, generate_report,
)


def load_config(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def build_nodes(cfg: dict) -> list[NodeHealth]:
    nodes: list[NodeHealth] = []
    for n in cfg.get("nodes", []):
        kind = n.get("type", "docker")
        name = n["name"]
        net = n.get("network", "?")
        if kind == "docker":
            nodes.append(DockerHealth(name, net, f"docker ps --filter name={name}"))
        elif kind == "systemd":
            nodes.append(SystemdHealth(name, net, f"systemctl is-active {name}"))
        else:
            raise ValueError(f"unknown node type: {kind}")
    return nodes


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--config", default=os.getenv("DEPIN_CONFIG", "config.yaml"))
    p.add_argument("--once", action="store_true", help="check once and exit")
    p.add_argument("--interval", type=int, default=60)
    p.add_argument("--snapshot", default="health.json")
    args = p.parse_args()

    cfg_path = Path(args.config)
    if not cfg_path.exists():
        # fall back to example
        cfg_path = Path(__file__).parent / "config.example.yaml"
    cfg = load_config(str(cfg_path))
    nodes = build_nodes(cfg)

    tg = TelegramAlerter.from_env()
    wh = None
    if cfg.get("alerts", {}).get("webhook", {}).get("enabled"):
        wh = WebhookAlerter(cfg["alerts"]["webhook"]["url"])

    last_status: dict[str, str] = {}
    while True:
        results = check_all(nodes)
        for r in results:
            prev = last_status.get(r["name"])
            if prev != r["status"]:
                # transition; alert
                if tg: tg.notify(name=r["name"], network=r["network"], status=r["status"], details=r["details"])
                if wh: wh.notify(name=r["name"], network=r["network"], status=r["status"], details=r["details"])
                last_status[r["name"]] = r["status"]
        # snapshot
        with open(args.snapshot, "w") as f:
            json.dump({"ts": int(time.time()), "results": results}, f, indent=2)
        if args.once:
            return 0
        time.sleep(args.interval)


if __name__ == "__main__":
    sys.exit(main())
