using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Yuki_PC
{
    public class YukiMessage
    {
        [JsonPropertyName("protocol")]
        public string Protocol { get; set; } = "yuki/1.1";

        [JsonPropertyName("type")]
        public string Type { get; set; }

        [JsonPropertyName("id")]
        public string Id { get; set; }

        [JsonPropertyName("timestamp")]
        public long Timestamp { get; set; } = DateTimeOffset.UtcNow.ToUnixTimeSeconds();

        [JsonPropertyName("payload")]
        public JsonElement Payload { get; set; }
    }

    public static class YukiProtocol
    {
        public static readonly JsonSerializerOptions SerializerOptions = new JsonSerializerOptions
        {
            PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
            WriteIndented = false
        };

        // ============ УПРАВЛЕНИЕ ПОДКЛЮЧЕНИЕМ ============

        public static YukiMessage CreateHelloMessage(string deviceId, string deviceType,
    string[] capabilities = null, string authToken = null,
    Dictionary<string, object> metadata = null)
        {
            var payload = new Dictionary<string, object>
            {
                ["device_id"] = deviceId,
                ["device_type"] = deviceType,
                ["capabilities"] = capabilities ?? Array.Empty<string>()
            };
            if (!string.IsNullOrEmpty(authToken))
                payload["auth_token"] = authToken;
            if (metadata != null)
                payload["metadata"] = metadata;

            return CreateMessage("hello", payload);
        }

        public static YukiMessage CreateWelcomeMessage(string sessionId, long serverTime,
            int heartbeatInterval = 30)
        {
            return CreateMessage("welcome", new
            {
                session_id = sessionId,
                server_time = serverTime,
                heartbeat_interval = heartbeatInterval
            });
        }

        // ============ СТАТУСЫ ============

        public static YukiMessage CreateStatusMessage(string deviceId, string status,
            Dictionary<string, object> details = null)
        {
            var payload = new Dictionary<string, object>
            {
                ["device_id"] = deviceId,
                ["status"] = status
            };
            if (details != null)
                payload["details"] = details;

            return CreateMessage("status", payload);
        }

        public static YukiMessage CreateExtendedStatusMessage(string deviceId,
            string status = null, string substatus = null,
            Dictionary<string, object> details = null)
        {
            var payload = new Dictionary<string, object>
            {
                ["device_id"] = deviceId
            };
            if (!string.IsNullOrEmpty(status))
                payload["status"] = status;
            if (!string.IsNullOrEmpty(substatus))
                payload["substatus"] = substatus;
            if (details != null)
                payload["details"] = details;

            return CreateMessage("extended_status", payload);
        }

        // ============ КОМАНДЫ ============

        public static YukiMessage CreateCommandMessage(string deviceId, string command,
            Dictionary<string, object> parameters = null)
        {
            return CreateMessage("command", new
            {
                device_id = deviceId,
                command = command,
                parameters = parameters ?? new Dictionary<string, object>()
            });
        }

        public static YukiMessage CreateCommandResultMessage(string originalId,
            bool success, object result = null, string error = null)
        {
            var msg = CreateMessage("command_result", new { success, result, error });
            msg.Id = originalId;
            return msg;
        }

        public static YukiMessage CreateConfirmCommandMessage(string deviceId,
            string command, Dictionary<string, object> parameters = null)
        {
            return CreateMessage("confirm_command", new
            {
                device_id = deviceId,
                command = command,
                parameters = parameters ?? new Dictionary<string, object>()
            });
        }

        public static YukiMessage CreateConfirmResponseMessage(string originalId,
            bool approved)
        {
            var msg = CreateMessage("confirm_response", new { approved });
            msg.Id = originalId;
            return msg;
        }

        // ============ УПРАВЛЕНИЕ УСТРОЙСТВАМИ ============

        public static YukiMessage CreateDevicesUpdateMessage(
            Dictionary<string, object> devices, string[] removed = null)
        {
            var payload = new Dictionary<string, object> { ["devices"] = devices };
            if (removed != null)
                payload["removed"] = removed;

            return CreateMessage("devices_update", payload);
        }

        public static YukiMessage CreateDeviceAuthRequestMessage(string deviceId,
            string deviceType, string[] capabilities)
        {
            return CreateMessage("device_auth_request", new
            {
                device_id = deviceId,
                device_type = deviceType,
                capabilities = capabilities
            });
        }

        public static YukiMessage CreateDeviceAuthResponseMessage(string requestId,
            bool approved)
        {
            var msg = CreateMessage("device_auth_response", new { approved });
            msg.Id = requestId;
            return msg;
        }

        // ============ ТОКЕНЫ ============

        public static YukiMessage CreateTokenUpdateMessage(string newToken,
            string reason = "admin")
        {
            return CreateMessage("token_update", new
            {
                new_token = newToken,
                reason = reason
            });
        }

        public static YukiMessage CreateTokenInfoMessage(long? createdAt,
            int rotationIntervalHours, long? expiresIn = null)
        {
            var payload = new Dictionary<string, object>
            {
                ["created_at"] = createdAt,
                ["rotation_interval_hours"] = rotationIntervalHours
            };
            if (expiresIn.HasValue)
                payload["expires_in"] = expiresIn.Value;

            return CreateMessage("token_info", payload);
        }

        public static YukiMessage CreateTokenRotatedMessage(bool success,
            string newToken = null)
        {
            var payload = new Dictionary<string, object> { ["success"] = success };
            if (!string.IsNullOrEmpty(newToken))
                payload["new_token"] = newToken;

            return CreateMessage("token_rotated", payload);
        }

        public static YukiMessage CreateRotateTokenRequestMessage()
        {
            return CreateMessage("rotate_token", new { });
        }

        public static YukiMessage CreateGetTokenInfoRequestMessage()
        {
            return CreateMessage("get_token_info", new { });
        }

        // ============ МЕТРИКИ ============

        public static YukiMessage CreateMetricsMessage(string deviceId,
            Dictionary<string, object> metrics)
        {
            return CreateMessage("metrics", new
            {
                device_id = deviceId,
                metrics = metrics,
                timestamp = DateTimeOffset.UtcNow.ToUnixTimeSeconds()
            });
        }

        public static YukiMessage CreateMetricsRequestMessage(string deviceId,
            string[] metricTypes = null)
        {
            return CreateMessage("metrics_request", new
            {
                device_id = deviceId,
                metric_types = metricTypes ?? Array.Empty<string>()
            });
        }

        // ============ СВЯЗЬ УСТРОЙСТВО–УСТРОЙСТВО ============

        public static YukiMessage CreateDeviceToDeviceMessage(string fromDeviceId,
            string toDeviceId, string command, object payload = null,
            bool requireResponse = false)
        {
            return CreateMessage("device_to_device", new
            {
                from_device_id = fromDeviceId,
                to_device_id = toDeviceId,
                command = command,
                payload = payload ?? new { },
                require_response = requireResponse,
                sent_at = DateTimeOffset.UtcNow.ToUnixTimeSeconds()
            });
        }

        public static YukiMessage CreateDeviceResponseMessage(string originalId,
            string fromDeviceId, string toDeviceId, bool success,
            object result = null, string error = null)
        {
            var msg = CreateMessage("device_response", new
            {
                from_device_id = fromDeviceId,
                to_device_id = toDeviceId,
                success = success,
                result = result,
                error = error
            });
            msg.Id = originalId;
            return msg;
        }

        public static YukiMessage CreateDeviceBroadcastMessage(string fromDeviceId,
            string command, object payload = null, string[] deviceFilter = null)
        {
            return CreateMessage("device_broadcast", new
            {
                from_device_id = fromDeviceId,
                command = command,
                payload = payload ?? new { },
                device_filter = deviceFilter,
                sent_at = DateTimeOffset.UtcNow.ToUnixTimeSeconds()
            });
        }

        // ============ ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ============

        private static YukiMessage CreateMessage(string type, object payload)
        {
            var json = JsonSerializer.Serialize(payload, SerializerOptions);
            return new YukiMessage
            {
                Type = type,
                Id = Guid.NewGuid().ToString(),
                Payload = JsonDocument.Parse(json).RootElement
            };
        }

        public static YukiMessage ParseMessage(string json)
        {
            return JsonSerializer.Deserialize<YukiMessage>(json, SerializerOptions);
        }

        public static string SerializeMessage(YukiMessage message)
        {
            return JsonSerializer.Serialize(message, SerializerOptions);
        }
    }
}