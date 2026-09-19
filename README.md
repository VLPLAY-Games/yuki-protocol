# Yuki Protocol

The shared wire protocol and SDK for the Yuki ecosystem. Every module (`yuki-core`, `yuki-webui`,
`yuki-device-pc`, `yuki-device-pc-linux`, `yuki-device-android`, `yuki-humidifier`) speaks this
protocol over WebSocket, either by depending on this repo directly (as a git submodule under a
`libs/yuki-protocol/` folder) or by implementing it in a language of its own.

Current version: **`yuki/1.0`**.

## Implementations

| Language | Path | Used by |
|---|---|---|
| Python | `python/yuki_protocol.py` | `yuki-core`, `yuki-webui`, `yuki-device-pc-linux` |
| C# | `csharp/YukiProtocol.cs` | `yuki-device-pc` |
| JavaScript | `javascript/yuki-protocol.js` | `yuki-webui` (browser) |
| C++ (ESP32/Arduino) | `esp32/Protocol.h` | `yuki-humidifier` |
| Kotlin | `kotlin/YukiMessage.kt`, `kotlin/YukiProtocol.kt` | `yuki-device-android` |

`yuki-device-android` keeps its own copy of the Kotlin files rather than pulling this repo in as a
submodule (Gradle/Android projects don't have a natural place to mount one) - the copy here is the
reference version; sync `yuki-device-android`'s copy by hand when either changes.

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

### Authenticating a device: two handshakes

`hello` supports either an `auth_token` field (legacy - the token travels on the wire, so only use
this over TLS or a fully trusted network) or a `nonce_c` field (challenge-response - the token never
travels at all):

```text
Legacy:            hello{auth_token}                                  -> welcome (or rejection)
Challenge-response: hello{nonce_c} -> challenge{nonce_s} -> auth{hmac} -> welcome (or rejection)
```

`hmac = HMAC-SHA256(token, "{nonce_c}:{nonce_s}")`, hex-encoded. `yuki-core` picks the method based
on whether `hello` carries `nonce_c` - a device can use either at any time, no server-side
per-device configuration needed. The Python implementation exposes both via `hello_message(...,
nonce_c=...)`, `challenge_message(nonce_s)` and `auth_message(hmac_value)`; other languages don't
have builder functions for `challenge`/`auth` yet (send/parse them as plain JSON matching the
envelope above until they do). Only `yuki-core` needs to issue `challenge` and verify `auth`, and a
device only needs to send them if it chooses to `nonce_c` at all, so this is purely additive and
doesn't affect any existing client that keeps using the legacy `auth_token` field.

## Extracting the ESP32 implementation

`esp32/Protocol.h` is the canonical C++ implementation, used by `yuki-humidifier`. It only builds
and sends messages (`sendStatus`, `sendMetrics`, `sendCommandResult`, ...) - the same split as the
other languages, where dispatch (deciding what a `command` *means*) lives in the consuming
application (`core.py`/`YukiClient.cs`/the humidifier's own `WebSocketHandler.h`), not in the
protocol layer itself. `yuki-humidifier` pulls this file in via the same git submodule mechanism as
every other consumer (`libs/yuki-protocol/esp32/Protocol.h`) - Arduino has no trouble compiling a
header reached through a relative subfolder path.

## Keeping submodule checkouts in sync

`yuki-core/libs/yuki-protocol/`, `yuki-device-pc/libs/yuki-protocol/`,
`yuki-device-pc-linux/libs/yuki-protocol/`, `yuki-humidifier/libs/yuki-protocol/` and
`yuki-webui/static/libs/yuki-protocol/` each carry this repo as a git submodule (`git submodule
update --init` to fetch it after cloning one of those).
When you change a message format here, push it to this repo and bump the submodule pointer (`git
submodule update --remote`, then commit the new pointer) in every consumer - there's no build step
or package registry tying them together, just the pinned commit each submodule points at.

## License

GNU General Public License v3.0 (GPLv3), same as the rest of the Yuki ecosystem - see
[yuki-system](https://github.com/VLPLAY-Games/yuki-system) for details.
