# DePIN Health Monitor

Automated health monitoring for DePIN nodes. Checks uptime, sync status, and earnings across multiple networks.

## Supported Networks
- Blockcast BEACON
- OptimAI Network
- Quip Network
- NARA Chain
- Nexus Prover

## Features
- Real-time node status checking
- Docker container health monitoring
- Alert notifications (Telegram/webhook)
- Historical uptime tracking
- Earnings estimation

## Usage
```bash
python3 monitor.py --config config.yaml
python3 monitor.py --check-all
python3 monitor.py --telegram-alerts
```

## Setup
```bash
pip install -r requirements.txt
cp config.example.yaml config.yaml
# Edit config.yaml with your node details
python3 monitor.py --init
```
