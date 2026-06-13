# depin-health-monitor

Real, working health monitor for a fleet of DePIN nodes. It:

- Polls a YAML-configured set of nodes (docker or systemd)
- Reports status transitions (healthy <-> degraded/unhealthy)
- Posts to Telegram and/or a generic JSON webhook
- Writes a `health.json` snapshot every cycle
- Runs as a long-lived daemon or as a one-shot checker

## Files

| File | Purpose |
|---|---|
| `monitor.py` | core: `NodeHealth`, `DockerHealth`, `SystemdHealth`, `check_all`, `generate_report` |
| `alerter.py`  | `TelegramAlerter` (with per-status throttling) + `WebhookAlerter` |
| `daemon.py`   | long-running loop, YAML config, snapshot writer |
| `config.example.yaml` | sample config for 5 DePIN nodes |
| `nodes/__init__.py` `nodes/blockcast.py` `nodes/optimai.py` | per-network adapters |
| `patterns.py` `flashbots.py` | extra helpers kept from earlier work |
| `requirements.txt`, `README.md` | this file |

## Quick start

```bash
pip install -r requirements.txt
export TG_BOT=12345:abcdef...
export TG_CHAT=1216419228

# one-shot
python3 daemon.py --once --config config.yaml

# daemon
python3 daemon.py --config config.yaml
```

## Telegram message format

```
🔴 nexus.service (Nexus): `unhealthy`
   service_status: inactive
   since: Mon 2026-06-13 12:00:00 UTC
```

## License

MIT
