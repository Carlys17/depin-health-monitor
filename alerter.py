"""Telegram alerter for the DePIN monitor. Posts a message on status
transitions (healthy <-> unhealthy/degraded) to a given chat.

Usage:
    from alerter import TelegramAlerter
    a = TelegramAlerter(bot_token=..., chat_id=...)
    a.notify(name="nexus", network="Nexus", status="unhealthy",
             details={"peers": 0, "height": 12345})
"""
from __future__ import annotations
import os
import time
import urllib.error
import urllib.request
import json
from typing import Optional


class TelegramAlerter:
    BASE = "https://api.telegram.org/bot{token}/{method}"

    def __init__(self, bot_token: str, chat_id: str, throttle_sec: int = 60):
        self.token = bot_token
        self.chat_id = chat_id
        self.throttle_sec = throttle_sec
        self._last_sent: dict[str, float] = {}

    @classmethod
    def from_env(cls) -> Optional["TelegramAlerter"]:
        t = os.getenv("TG_BOT")
        c = os.getenv("TG_CHAT")
        if not t or not c:
            return None
        return cls(t, c)

    def notify(self, *, name: str, network: str, status: str, details: dict | None = None,
               force: bool = False) -> bool:
        key = f"{name}:{status}"
        now = time.time()
        if not force and (now - self._last_sent.get(key, 0)) < self.throttle_sec:
            return False

        emoji = {"healthy": "✅", "degraded": "⚠️", "unhealthy": "🔴", "error": "❌", "timeout": "⏰"}.get(status, "❓")
        lines = [f"{emoji} *{name}* ({network}): `{status}`"]
        if details:
            for k, v in list(details.items())[:8]:
                lines.append(f"   {k}: `{v}`")
        text = "\n".join(lines)
        try:
            url = self.BASE.format(token=self.token, method="sendMessage")
            body = json.dumps({"chat_id": self.chat_id, "text": text, "parse_mode": "Markdown"}).encode()
            req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=10).read()
            self._last_sent[key] = now
            return True
        except urllib.error.URLError as e:
            print(f"[alerter] telegram send failed: {e}", flush=True)
            return False


class WebhookAlerter:
    """Generic JSON webhook (Discord, Slack-compatible, etc.)."""

    def __init__(self, url: str, throttle_sec: int = 60):
        self.url = url
        self.throttle_sec = throttle_sec
        self._last_sent: dict[str, float] = {}

    def notify(self, *, name: str, network: str, status: str, details: dict | None = None) -> bool:
        key = f"{name}:{status}"
        now = time.time()
        if (now - self._last_sent.get(key, 0)) < self.throttle_sec:
            return False
        body = json.dumps({
            "name": name, "network": network, "status": status, "details": details or {},
            "ts": int(now),
        }).encode()
        try:
            req = urllib.request.Request(self.url, data=body, headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=10).read()
            self._last_sent[key] = now
            return True
        except urllib.error.URLError as e:
            print(f"[alerter] webhook send failed: {e}", flush=True)
            return False
