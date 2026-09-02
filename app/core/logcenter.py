"""Singleton do LogCenter SDK para uso em toda a aplicação"""

from __future__ import annotations

from typing import Optional

from logcenter_sdk import LogCenterConfig, LogCenterSender

_sender: Optional[LogCenterSender] = None


def init_logcenter(base_url: str, project_id: str, api_key: Optional[str] = None) -> LogCenterSender:
    global _sender
    cfg = LogCenterConfig(base_url=base_url, project_id=project_id, api_key=api_key)
    _sender = LogCenterSender(cfg)
    return _sender


def get_sender() -> Optional[LogCenterSender]:
    return _sender
