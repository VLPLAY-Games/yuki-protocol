#ifndef YUKI_PROTOCOL_ESP32_H
#define YUKI_PROTOCOL_ESP32_H

// Yuki Protocol v1.0 - ESP32/Arduino (C++) implementation. Message building/sending only; dispatch is the firmware's job.

#include <WebSocketsClient.h>
#include <ArduinoJson.h>
#include <esp_mac.h>

#ifndef PROTOCOL_VERSION
#define PROTOCOL_VERSION "yuki/1.0"
#endif

extern WebSocketsClient webSocket;
extern bool webSocketConnected;

// Implemented by the including firmware (its configured device id).
String getYukiDeviceId();

// ==================== ID GENERATION ====================
String generateId() {
  char id[37];
  uint8_t mac[6];
  esp_efuse_mac_get_default(mac);

  snprintf(id, sizeof(id), "%02x%02x%02x%02x%02x%02x%08lx",
           mac[0], mac[1], mac[2], mac[3], mac[4], mac[5],
           (unsigned long)millis());
  return String(id);
}

// ==================== BASE SEND ====================
void sendRawMessage(String type, JsonObject& payload, String msgId = "") {
  if (!webSocketConnected) {
    Serial.println("[WS] Cannot send message, not connected");
    return;
  }

  StaticJsonDocument<2048> doc;
  doc["protocol"] = PROTOCOL_VERSION;
  doc["type"] = type;
  doc["id"] = msgId.length() > 0 ? msgId : generateId();
  doc["timestamp"] = (int)(millis() / 1000);

  JsonObject payloadObj = doc.createNestedObject("payload");
  payloadObj.set(payload);

  String output;
  serializeJson(doc, output);
  webSocket.sendTXT(output);
  Serial.printf("[WS] Sent: %s\n", output.c_str());
}

void sendMessage(String type, JsonObject& payload) {
  sendRawMessage(type, payload, "");
}

// ==================== CONNECTION ====================
void sendHello(String deviceType, JsonArray& capabilities,
               JsonObject* metadata = nullptr, String authToken = "") {
  StaticJsonDocument<1024> doc;
  doc["protocol"] = PROTOCOL_VERSION;
  doc["type"] = "hello";
  doc["id"] = generateId();
  doc["timestamp"] = (int)(millis() / 1000);

  JsonObject payloadObj = doc.createNestedObject("payload");
  payloadObj["device_id"] = getYukiDeviceId();
  payloadObj["device_type"] = deviceType;
  if (authToken.length() > 0) {
    payloadObj["auth_token"] = authToken;
  }

  JsonArray capsOut = payloadObj.createNestedArray("capabilities");
  for (JsonVariant v : capabilities) {
    capsOut.add(v);
  }

  if (metadata != nullptr) {
    JsonObject metaOut = payloadObj.createNestedObject("metadata");
    metaOut.set(*metadata);
  }

  String output;
  serializeJson(doc, output);
  webSocket.sendTXT(output);
  Serial.println("[WS] Hello sent, waiting for welcome...");
}

// ==================== STATUS ====================
void sendStatus(String status, String details) {
  StaticJsonDocument<512> payload;
  payload["device_id"] = getYukiDeviceId();
  payload["status"] = status;
  if (details.length() > 0) {
    payload["details"] = details;
  }

  StaticJsonDocument<512> wrapper;
  JsonObject payloadObj = wrapper.to<JsonObject>();
  payloadObj.set(payload.as<JsonObject>());
  sendMessage("status", payloadObj);
}

void sendExtendedStatus(String substatus, JsonObject& details) {
  StaticJsonDocument<1024> payload;
  payload["device_id"] = getYukiDeviceId();
  payload["status"] = "online";
  payload["substatus"] = substatus;

  JsonObject detailsObj = payload.createNestedObject("details");
  detailsObj.set(details);

  StaticJsonDocument<1024> wrapper;
  JsonObject payloadObj = wrapper.to<JsonObject>();
  payloadObj.set(payload.as<JsonObject>());
  sendMessage("extended_status", payloadObj);

  Serial.printf("[WS] Extended status: %s\n", substatus.c_str());
}

// ==================== METRICS ====================
// Firmware builds its own metrics object, mirroring metrics_message() in python/js/csharp.
void sendMetrics(JsonObject& metrics) {
  StaticJsonDocument<1024> payload;
  payload["device_id"] = getYukiDeviceId();

  JsonObject metricsObj = payload.createNestedObject("metrics");
  metricsObj.set(metrics);

  payload["timestamp"] = (int)(millis() / 1000);

  StaticJsonDocument<1024> wrapper;
  JsonObject payloadObj = wrapper.to<JsonObject>();
  payloadObj.set(payload.as<JsonObject>());
  sendMessage("metrics", payloadObj);

  Serial.println("[WS] Metrics sent");
}

// ==================== COMMANDS ====================
void sendCommandResult(String cmdId, bool success, JsonObject& result, String error = "") {
  String output;
  StaticJsonDocument<1024> doc;
  doc["protocol"] = PROTOCOL_VERSION;
  doc["type"] = "command_result";
  doc["id"] = cmdId;
  doc["timestamp"] = (int)time(NULL);

  JsonObject payload = doc.createNestedObject("payload");
  payload["success"] = success;
  if (success && !result.isNull()) {
    payload["result"] = result;
  }
  if (!success && error.length() > 0) {
    payload["error"] = error;
  }

  serializeJson(doc, output);
  webSocket.sendTXT(output);
}

void sendCommandResult(String cmdId, bool success, String error = "") {
  StaticJsonDocument<128> emptyResult;
  JsonObject emptyObj = emptyResult.to<JsonObject>();
  sendCommandResult(cmdId, success, emptyObj, error);
}

// ==================== DEVICE <-> DEVICE ====================
void sendToDevice(String targetDeviceId, String command, JsonObject& params, bool requireResponse = false) {
  StaticJsonDocument<1024> payload;
  payload["from_device_id"] = getYukiDeviceId();
  payload["to_device_id"] = targetDeviceId;
  payload["command"] = command;
  payload["require_response"] = requireResponse;

  JsonObject paramsObj = payload.createNestedObject("payload");
  paramsObj.set(params);

  StaticJsonDocument<1024> wrapper;
  JsonObject payloadObj = wrapper.to<JsonObject>();
  payloadObj.set(payload.as<JsonObject>());
  sendMessage("device_to_device", payloadObj);

  Serial.printf("[WS] Sent to device %s: %s\n", targetDeviceId.c_str(), command.c_str());
}

void broadcastToDevices(String command, JsonObject& params, JsonArray& deviceFilter) {
  StaticJsonDocument<1024> payload;
  payload["from_device_id"] = getYukiDeviceId();
  payload["command"] = command;

  JsonObject paramsObj = payload.createNestedObject("payload");
  paramsObj.set(params);

  if (!deviceFilter.isNull()) {
    payload["device_filter"] = deviceFilter;
  }

  StaticJsonDocument<1024> wrapper;
  JsonObject payloadObj = wrapper.to<JsonObject>();
  payloadObj.set(payload.as<JsonObject>());
  sendMessage("device_broadcast", payloadObj);

  Serial.printf("[WS] Broadcast: %s\n", command.c_str());
}

// Answers a device_command/device_broadcast, mirroring device_response_message() in python/js/csharp.
void sendDeviceResponse(String msgId, String fromDeviceId, String toDeviceId,
                         bool success, String error = "") {
  StaticJsonDocument<512> payload;
  payload["from_device_id"] = fromDeviceId;
  payload["to_device_id"] = toDeviceId;
  payload["success"] = success;
  if (!success && error.length() > 0) {
    payload["error"] = error;
  }

  StaticJsonDocument<512> wrapper;
  JsonObject payloadObj = wrapper.to<JsonObject>();
  payloadObj.set(payload.as<JsonObject>());
  sendRawMessage("device_response", payloadObj, msgId);
}

template<typename T>
void sendDeviceResponse(String msgId, String fromDeviceId, String toDeviceId,
                         bool success, T result, String error = "") {
  StaticJsonDocument<512> payload;
  payload["from_device_id"] = fromDeviceId;
  payload["to_device_id"] = toDeviceId;
  payload["success"] = success;
  payload["result"] = result;
  if (!success && error.length() > 0) {
    payload["error"] = error;
  }

  StaticJsonDocument<512> wrapper;
  JsonObject payloadObj = wrapper.to<JsonObject>();
  payloadObj.set(payload.as<JsonObject>());
  sendRawMessage("device_response", payloadObj, msgId);
}

#endif
