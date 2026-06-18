// yuki-protocol.js – Унифицированный протокол Yuki v1.1 для JavaScript

const PROTOCOL_VERSION = "yuki/1.1";

class YukiMessage {
    constructor(type, payload, id = null) {
        this.protocol = PROTOCOL_VERSION;
        this.type = type;
        this.id = id || crypto.randomUUID();
        this.timestamp = Math.floor(Date.now() / 1000);
        this.payload = payload;
    }

    toJSON() {
        return {
            protocol: this.protocol,
            type: this.type,
            id: this.id,
            timestamp: this.timestamp,
            payload: this.payload
        };
    }

    toString() {
        return JSON.stringify(this.toJSON());
    }

    static fromJSON(data) {
        const obj = typeof data === 'string' ? JSON.parse(data) : data;
        if (!obj.protocol || !obj.protocol.startsWith('yuki/')) {
            throw new Error(`Unsupported protocol: ${obj.protocol}`);
        }
        const msg = new YukiMessage(obj.type, obj.payload || {}, obj.id);
        msg.timestamp = obj.timestamp || msg.timestamp;
        return msg;
    }
}

// ============ ВСЕ ФУНКЦИИ СОЗДАНИЯ СООБЩЕНИЙ ============

function helloMessage(deviceId, deviceType, capabilities = [], metadata = null, authToken = null) {
    const payload = {
        device_id: deviceId,
        device_type: deviceType,
        capabilities: capabilities
    };
    if (metadata) payload.metadata = metadata;
    if (authToken) payload.auth_token = authToken;
    return new YukiMessage('hello', payload);
}

function welcomeMessage(sessionId, serverTime, heartbeatInterval = 30) {
    return new YukiMessage('welcome', {
        session_id: sessionId,
        server_time: serverTime,
        heartbeat_interval: heartbeatInterval
    });
}

function statusMessage(deviceId, status, details = null) {
    const payload = { device_id: deviceId, status };
    if (details) payload.details = details;
    return new YukiMessage('status', payload);
}

function extendedStatusMessage(deviceId, status = null, substatus = null, details = null) {
    const payload = { device_id: deviceId };
    if (status) payload.status = status;
    if (substatus) payload.substatus = substatus;
    if (details) payload.details = details;
    return new YukiMessage('extended_status', payload);
}

function commandMessage(deviceId, command, params = {}) {
    return new YukiMessage('command', {
        device_id: deviceId,
        command: command,
        params: params
    });
}

function commandResultMessage(originalId, success, result = null, error = null) {
    const msg = new YukiMessage('command_result', {
        success: success,
        result: result,
        error: error
    });
    msg.id = originalId;
    return msg;
}

function confirmCommandMessage(deviceId, command, params = {}) {
    return new YukiMessage('confirm_command', {
        device_id: deviceId,
        command: command,
        params: params
    });
}

function confirmResponseMessage(originalId, approved) {
    const msg = new YukiMessage('confirm_response', { approved: approved });
    msg.id = originalId;
    return msg;
}

function devicesUpdateMessage(devices, removed = null) {
    const payload = { devices: devices };
    if (removed) payload.removed = removed;
    return new YukiMessage('devices_update', payload);
}

function deviceAuthRequestMessage(deviceId, deviceType, capabilities) {
    return new YukiMessage('device_auth_request', {
        device_id: deviceId,
        device_type: deviceType,
        capabilities: capabilities
    });
}

function deviceAuthResponseMessage(requestId, approved) {
    const msg = new YukiMessage('device_auth_response', { approved: approved });
    msg.id = requestId;
    return msg;
}

function tokenUpdateMessage(newToken, reason = 'admin') {
    return new YukiMessage('token_update', {
        new_token: newToken,
        reason: reason
    });
}

function tokenInfoMessage(createdAt, rotationIntervalHours, expiresIn = null) {
    const payload = {
        created_at: createdAt,
        rotation_interval_hours: rotationIntervalHours
    };
    if (expiresIn !== null) payload.expires_in = expiresIn;
    return new YukiMessage('token_info', payload);
}

function tokenRotatedMessage(success, newToken = null) {
    const payload = { success: success };
    if (newToken) payload.new_token = newToken;
    return new YukiMessage('token_rotated', payload);
}

function rotateTokenRequestMessage() {
    return new YukiMessage('rotate_token', {});
}

function getTokenInfoRequestMessage() {
    return new YukiMessage('get_token_info', {});
}

function metricsMessage(deviceId, metrics) {
    return new YukiMessage('metrics', {
        device_id: deviceId,
        metrics: metrics,
        timestamp: Math.floor(Date.now() / 1000)
    });
}

function metricsRequestMessage(deviceId, metricTypes = []) {
    return new YukiMessage('metrics_request', {
        device_id: deviceId,
        metric_types: metricTypes
    });
}

function deviceToDeviceMessage(fromDeviceId, toDeviceId, command, payload = {}, requireResponse = false) {
    return new YukiMessage('device_to_device', {
        from_device_id: fromDeviceId,
        to_device_id: toDeviceId,
        command: command,
        payload: payload,
        require_response: requireResponse,
        sent_at: Math.floor(Date.now() / 1000)
    });
}

function deviceResponseMessage(originalId, fromDeviceId, toDeviceId, success, result = null, error = null) {
    const msg = new YukiMessage('device_response', {
        from_device_id: fromDeviceId,
        to_device_id: toDeviceId,
        success: success,
        result: result,
        error: error
    });
    msg.id = originalId;
    return msg;
}

function deviceBroadcastMessage(fromDeviceId, command, payload = {}, deviceFilter = null) {
    return new YukiMessage('device_broadcast', {
        from_device_id: fromDeviceId,
        command: command,
        payload: payload,
        device_filter: deviceFilter,
        sent_at: Math.floor(Date.now() / 1000)
    });
}

// ============ ЗАПРОСЫ ДЛЯ WEBUI ============

function getDevicesRequestMessage() {
    return new YukiMessage('get_devices', {});
}

function broadcastCommandMessage(command, payload = {}) {
    return new YukiMessage('broadcast_command', { command, payload });
}

function getSystemMetricsRequestMessage() {
    return new YukiMessage('get_system_metrics', {});
}

function getBlacklistRequestMessage() {
    return new YukiMessage('get_blacklist', {});
}

function getAuditLogRequestMessage(limit = 500) {
    return new YukiMessage('get_audit_log', { limit });
}

function disconnectDeviceMessage(deviceId) {
    return new YukiMessage('disconnect_device', { device_id: deviceId });
}

function removeDeviceMessage(deviceId) {
    return new YukiMessage('remove_device', { device_id: deviceId });
}

function blacklistAddMessage(deviceId) {
    return new YukiMessage('blacklist_add', { device_id: deviceId });
}

function blacklistRemoveMessage(deviceId) {
    return new YukiMessage('blacklist_remove', { device_id: deviceId });
}

function getExtendedStatusesRequestMessage() {
    return new YukiMessage('get_extended_statuses', {});
}

function getDeviceMetricsRequestMessage(deviceId, hours, metrics) {
    return new YukiMessage('get_device_metrics', {
        device_id: deviceId,
        hours: hours,
        metrics: metrics
    });
}

function requestDeviceMetricsMessage(deviceId, metricTypes = null) {
    return new YukiMessage('request_device_metrics', {
        device_id: deviceId,
        metric_types: metricTypes
    });
}