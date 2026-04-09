"""
Yuki Protocol v1.0 – общая реализация для всех компонентов системы.
"""

import json
import time
import uuid
from typing import Optional, Dict, Any, List

PROTOCOL_VERSION = "yuki/1.0"

class YukiMessage:
    """Базовый класс для всех сообщений протокола."""
    def __init__(self, msg_type: str, payload: Dict[str, Any], msg_id: Optional[str] = None):
        self.protocol = PROTOCOL_VERSION
        self.type = msg_type
        self.id = msg_id or str(uuid.uuid4())
        self.timestamp = int(time.time())
        self.payload = payload

    def to_json(self) -> str:
        return json.dumps({
            "protocol": self.protocol,
            "type": self.type,
            "id": self.id,
            "timestamp": self.timestamp,
            "payload": self.payload
        })

    @classmethod
    def from_json(cls, data: str) -> "YukiMessage":
        obj = json.loads(data)
        if obj.get("protocol") != PROTOCOL_VERSION:
            raise ValueError(f"Unsupported protocol version: {obj.get('protocol')}")
        msg = cls(obj["type"], obj.get("payload", {}), obj.get("id"))
        msg.timestamp = obj.get("timestamp", msg.timestamp)
        return msg


def hello_message(device_id: str, device_type: str, capabilities: List[str] = None, metadata: Dict = None) -> YukiMessage:
    payload = {
        "device_id": device_id,
        "device_type": device_type
    }
    if capabilities:
        payload["capabilities"] = capabilities
    if metadata:
        payload["metadata"] = metadata
    return YukiMessage("hello", payload)


def welcome_message(session_id: str, server_time: int, heartbeat_interval: int = 30) -> YukiMessage:
    payload = {
        "session_id": session_id,
        "server_time": server_time,
        "heartbeat_interval": heartbeat_interval
    }
    return YukiMessage("welcome", payload)


def command_message(device_id: str, command: str, params: Dict = None) -> YukiMessage:
    payload = {
        "device_id": device_id,
        "command": command,
        "params": params or {}
    }
    return YukiMessage("command", payload)


def command_result_message(original_id: str, success: bool, result: Any = None, error: str = None) -> YukiMessage:
    payload = {
        "success": success,
        "result": result,
        "error": error
    }
    msg = YukiMessage("command_result", payload)
    msg.id = original_id
    return msg


def status_message(device_id: str, status: str, details: Dict = None) -> YukiMessage:
    payload = {
        "device_id": device_id,
        "status": status
    }
    if details:
        payload["details"] = details
    return YukiMessage("status", payload)


def devices_update_message(devices: Dict[str, Dict], removed: List[str] = None) -> YukiMessage:
    payload = {"devices": devices}
    if removed:
        payload["removed"] = removed
    return YukiMessage("devices_update", payload)