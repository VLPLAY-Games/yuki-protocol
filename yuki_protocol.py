"""
Yuki Protocol v1.1 – добавлены сообщения для управления авторизацией устройств,
ротации токенов и информации о токене.
"""
import json
import time
import uuid
from typing import Optional, Dict, Any, List

PROTOCOL_VERSION = "yuki/1.1"

class YukiMessage:
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
        if obj.get("protocol") not in ["yuki/1.0", "yuki/1.1"]:
            raise ValueError(f"Unsupported protocol version: {obj.get('protocol')}")
        msg = cls(obj["type"], obj.get("payload", {}), obj.get("id"))
        msg.timestamp = obj.get("timestamp", msg.timestamp)
        return msg


def hello_message(device_id: str, device_type: str, capabilities: List[str] = None,
                  metadata: Dict = None, auth_token: str = None) -> YukiMessage:
    payload = {
        "device_id": device_id,
        "device_type": device_type
    }
    if capabilities:
        payload["capabilities"] = capabilities
    if metadata:
        payload["metadata"] = metadata
    if auth_token:
        payload["auth_token"] = auth_token
    return YukiMessage("hello", payload)


def welcome_message(session_id: str, server_time: int, heartbeat_interval: int = 30) -> YukiMessage:
    return YukiMessage("welcome", {
        "session_id": session_id,
        "server_time": server_time,
        "heartbeat_interval": heartbeat_interval
    })


def command_message(device_id: str, command: str, params: Dict = None) -> YukiMessage:
    return YukiMessage("command", {
        "device_id": device_id,
        "command": command,
        "params": params or {}
    })


def command_result_message(original_id: str, success: bool, result: Any = None, error: str = None) -> YukiMessage:
    msg = YukiMessage("command_result", {
        "success": success,
        "result": result,
        "error": error
    })
    msg.id = original_id
    return msg


def status_message(device_id: str, status: str, details: Dict = None) -> YukiMessage:
    payload = {"device_id": device_id, "status": status}
    if details:
        payload["details"] = details
    return YukiMessage("status", payload)


def devices_update_message(devices: Dict[str, Dict], removed: List[str] = None) -> YukiMessage:
    payload = {"devices": devices}
    if removed:
        payload["removed"] = removed
    return YukiMessage("devices_update", payload)


def confirm_command_message(device_id: str, command: str, params: Dict = None) -> YukiMessage:
    return YukiMessage("confirm_command", {
        "device_id": device_id,
        "command": command,
        "params": params or {}
    })


def confirm_response_message(original_id: str, approved: bool) -> YukiMessage:
    msg = YukiMessage("confirm_response", {"approved": approved})
    msg.id = original_id
    return msg


def device_auth_request_message(device_id: str, device_type: str, capabilities: List[str]) -> YukiMessage:
    """Запрос авторизации нового устройства (Core -> WebUI)."""
    return YukiMessage("device_auth_request", {
        "device_id": device_id,
        "device_type": device_type,
        "capabilities": capabilities
    })


def device_auth_response_message(request_id: str, approved: bool) -> YukiMessage:
    """Ответ WebUI на запрос авторизации."""
    msg = YukiMessage("device_auth_response", {"approved": approved})
    msg.id = request_id
    return msg


# ------------------- Новые сообщения для ротации токенов -------------------

def token_update_message(new_token: str, reason: str = "admin") -> YukiMessage:
    """
    Сообщение от сервера к устройству с новым токеном.
    Устройство должно сохранить этот токен и использовать при последующих подключениях.
    """
    return YukiMessage("token_update", {
        "new_token": new_token,
        "reason": reason
    })


def token_info_message(created_at: Optional[float], rotation_interval_hours: int,
                       expires_in: Optional[float] = None) -> YukiMessage:
    """
    Информация о текущем токене (отправляется сервером в ответ на запрос get_token_info).
    """
    payload = {
        "created_at": created_at,
        "rotation_interval_hours": rotation_interval_hours,
        "expires_in": expires_in
    }
    return YukiMessage("token_info", payload)


def token_rotated_message(success: bool, new_token: Optional[str] = None) -> YukiMessage:
    """
    Ответ сервера на команду rotate_token (WebUI -> Core).
    Сообщает об успешной или неудачной ротации.
    """
    payload = {"success": success}
    if new_token:
        payload["new_token"] = new_token
    return YukiMessage("token_rotated", payload)


# ------------------- Вспомогательные команды для WebUI -------------------

def rotate_token_request_message() -> YukiMessage:
    """
    Запрос от WebUI к серверу на принудительную ротацию токена.
    """
    return YukiMessage("rotate_token", {})


def get_token_info_request_message() -> YukiMessage:
    """
    Запрос от WebUI к серверу на получение информации о токене.
    """
    return YukiMessage("get_token_info", {})