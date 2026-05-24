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

# ==================== ДЛЯ РАСШИРЕННОГО СТАТУСА ====================

def extended_status_message(device_id: str, status: str, substatus: str = None, 
                           details: Dict = None) -> YukiMessage:
    """
    Расширенный статус устройства.
    status: основной статус (online/offline/pending)
    substatus: дополнительный (idle, working, sleeping, charging, error, updating)
    details: дополнительная информация
    """
    payload = {
        "device_id": device_id,
        "status": status,
        "substatus": substatus,
        "details": details or {}
    }
    return YukiMessage("extended_status", payload)


# ==================== ДЛЯ МЕТРИК ====================

def metrics_message(device_id: str, metrics: Dict) -> YukiMessage:
    """
    Унифицированное сообщение с метриками.
    metrics: {
        "cpu": 45.2,           # % (для ПК/ESP)
        "memory": 1024,        # MB used
        "memory_percent": 32.5,# %
        "temperature": 23.5,   # °C (для увлажнителя/ESP)
        "humidity": 55.0,      # % (для увлажнителя)
        "battery": 85,         # % (для мобильных)
        "uptime": 86400,       # seconds
        "disk_used": 500,      # GB
        "disk_total": 1000,    # GB
        "network_rx": 1024,    # KB/s
        "network_tx": 512,     # KB/s
        "water_level": 70,     # % (для увлажнителя)
        "fan_speed": 3,        # уровень
        "custom": {}           # любые кастомные метрики
    }
    """
    return YukiMessage("metrics", {
        "device_id": device_id,
        "metrics": metrics,
        "timestamp": int(time.time())
    })


def metrics_request_message(device_id: str, metric_types: List[str] = None) -> YukiMessage:
    """Запрос метрик от устройства"""
    return YukiMessage("metrics_request", {
        "device_id": device_id,
        "metric_types": metric_types or []
    })


# ==================== ДЛЯ СВЯЗИ УСТРОЙСТВО->УСТРОЙСТВО ====================

def device_to_device_message(from_device_id: str, to_device_id: str, 
                             command: str, payload: Dict = None,
                             require_response: bool = False) -> YukiMessage:
    """
    Отправка команды от одного устройства другому через ядро.
    """
    return YukiMessage("device_to_device", {
        "from_device_id": from_device_id,
        "to_device_id": to_device_id,
        "command": command,
        "payload": payload or {},
        "require_response": require_response,
        "sent_at": int(time.time())
    })


def device_response_message(original_id: str, from_device_id: str, 
                           to_device_id: str, success: bool, 
                           result: Any = None, error: str = None) -> YukiMessage:
    """Ответ от устройства на запрос от другого устройства"""
    msg = YukiMessage("device_response", {
        "from_device_id": from_device_id,
        "to_device_id": to_device_id,
        "success": success,
        "result": result,
        "error": error
    })
    msg.id = original_id
    return msg


def device_broadcast_message(from_device_id: str, command: str, 
                            payload: Dict = None, device_filter: List[str] = None) -> YukiMessage:
    """Широковещательная команда от устройства всем (или фильтрованным) устройствам"""
    return YukiMessage("device_broadcast", {
        "from_device_id": from_device_id,
        "command": command,
        "payload": payload or {},
        "device_filter": device_filter,  # None = всем, иначе список ID
        "sent_at": int(time.time())
    })
