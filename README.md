# Yuki Protocol

The shared wire protocol and SDK for the Yuki ecosystem. Every module (`yuki-core`, `yuki-webui`,
`yuki-device-pc`, `yuki-device-pc-linux`, `yuki-device-android`, `yuki-humidifier`) speaks this
protocol over WebSocket, either by depending on this repo directly (as a vendored copy under a
`libs/yuki-protocol/` folder) or by implementing it in a language of its own.

Current version: **`yuki/1.0`**.

## Implementations

| Language | Path | Used by |
|---|---|---|
| Python | `python/yuki_protocol.py` | `yuki-core`, `yuki-webui`, `yuki-device-pc-linux` |
| C# | `csharp/YukiProtocol.cs` | `yuki-device-pc` |
| JavaScript | `javascript/yuki-protocol.js` | `yuki-webui` (browser) |
| C++ (ESP32/Arduino) | `esp32/Protocol.h` | `yuki-humidifier` |

Android (`yuki-device-android`) implements the same protocol in Kotlin directly in its own repo
(`YukiMessage.kt`/`YukiProtocol.kt`) rather than vendoring this one, since Kotlin/Gson has no
natural place to live inside this repo's per-language folders yet.

## Message format

Every message is a single JSON object, no binary framing, no checksum:

```json
{
  "protocol": "yuki/1.0",
  "type": "hello",
  "id": "a uuid4 (or device-generated id on ESP32)",
  "timestamp": 1730000000,
  "payload": { "...": "type-specific fields" }
}
```

Message types cover connection setup (`hello`/`welcome`), status (`status`/`extended_status`),
commands (`command`/`command_result`, with an optional `confirm_command`/`confirm_response`
round-trip for dangerous commands), device management and auth (`devices_update`,
`device_auth_request`/`device_auth_response`), token rotation (`token_update`, `token_info`,
`rotate_token`, ...), metrics (`metrics`, `metrics_request`), and device-to-device relaying
(`device_to_device`, `device_response`, `device_broadcast`). The JavaScript implementation also
has a handful of WebUI-only request messages (`get_devices`, `get_blacklist`, ...) that the other
languages don't need.

Every implementation stamps and validates the `protocol` field as `yuki/1.0` and rejects anything
else - there is no version-negotiation handshake, so all modules in a deployment must run the same
protocol major version.

## Extracting the ESP32 implementation

`esp32/Protocol.h` is the canonical C++ implementation, used by `yuki-humidifier`. It only builds
and sends messages (`sendStatus`, `sendMetrics`, `sendCommandResult`, ...) - the same split as the
other languages, where dispatch (deciding what a `command` *means*) lives in the consuming
application (`core.py`/`YukiClient.cs`/the humidifier's own `WebSocketHandler.h`), not in the
protocol layer itself. `yuki-humidifier/Protocol.h` is a synced copy of this file; keep them
identical when editing either.

## Keeping vendored copies in sync

`yuki-core/libs/yuki-protocol/`, `yuki-device-pc/libs/yuki-protocol/` and
`yuki-webui/static/libs/yuki-protocol/` each carry a copy of the relevant language folder(s) from
this repo. When you change a message format here, copy the change into every vendored copy that
uses that language - there's no build step or package registry tying them together.
