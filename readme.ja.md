# Yuki Protocol

Yuki エコシステムが共有する通信プロトコルおよび SDK です。すべてのモジュール（`yuki-core`、`yuki-webui`、`yuki-device-pc`、`yuki-device-pc-linux`、`yuki-device-android`、`yuki-humidifier`）は、このリポジトリに直接依存する形（`libs/yuki-protocol/` フォルダ配下への同梱コピー）で、あるいは独自の言語で実装する形で、WebSocket 上でこのプロトコルを使用します。

現行バージョン: **`yuki/1.0`**

## 実装

| 言語 | パス | 利用元 |
|---|---|---|
| Python | `python/yuki_protocol.py` | `yuki-core`、`yuki-webui`、`yuki-device-pc-linux` |
| C# | `csharp/YukiProtocol.cs` | `yuki-device-pc` |
| JavaScript | `javascript/yuki-protocol.js` | `yuki-webui`（ブラウザ側） |
| C++（ESP32/Arduino） | `esp32/Protocol.h` | `yuki-humidifier` |

Android（`yuki-device-android`）は、このリポジトリを同梱する代わりに、同じプロトコルを Kotlin で自身のリポジトリ内に直接実装しています（`YukiMessage.kt`/`YukiProtocol.kt`）。Kotlin/Gson には、このリポジトリの言語別フォルダ構成の中に収まる自然な置き場所が今のところないためです。

## メッセージ形式

すべてのメッセージは単一の JSON オブジェクトであり、バイナリフレーミングもチェックサムもありません。

```json
{
  "protocol": "yuki/1.0",
  "type": "hello",
  "id": "a uuid4 (or device-generated id on ESP32)",
  "timestamp": 1730000000,
  "payload": { "...": "type-specific fields" }
}
```

メッセージタイプは、接続確立（`hello`/`welcome`）、ステータス（`status`/`extended_status`）、コマンド（`command`/`command_result`、危険なコマンドには任意で `confirm_command`/`confirm_response` の往復確認が付随）、デバイス管理・認証（`devices_update`、`device_auth_request`/`device_auth_response`）、トークンローテーション（`token_update`、`token_info`、`rotate_token` など）、メトリクス（`metrics`、`metrics_request`）、デバイス間中継（`device_to_device`、`device_response`、`device_broadcast`）をカバーします。JavaScript 実装には、他の言語では不要な WebUI 専用のリクエストメッセージ（`get_devices`、`get_blacklist` など）もいくつか存在します。

すべての実装は `protocol` フィールドに `yuki/1.0` をスタンプし検証した上で、それ以外を拒否します - バージョンネゴシエーションのハンドシェイクは存在しないため、1つのデプロイ内のすべてのモジュールは同じプロトコルメジャーバージョンで動作する必要があります。

## ESP32 実装の抜き出し

`esp32/Protocol.h` は `yuki-humidifier` が使用する正典的な C++ 実装です。メッセージの構築と送信のみを行い（`sendStatus`、`sendMetrics`、`sendCommandResult` など）、これは他の言語と同じ役割分担です。すなわち、ディスパッチ（`command` が*何を意味するか*を決定する処理）はプロトコル層自体ではなく、それを利用するアプリケーション側（`core.py`/`YukiClient.cs`/humidifier 自身の `WebSocketHandler.h`）に存在します。`yuki-humidifier/Protocol.h` はこのファイルの同期済みコピーです。どちらかを編集する際は、両者を同一内容に保ってください。

## 同梱コピーの同期を保つ

`yuki-core/libs/yuki-protocol/`、`yuki-device-pc/libs/yuki-protocol/`、`yuki-webui/static/libs/yuki-protocol/` は、それぞれこのリポジトリ内の該当する言語フォルダのコピーを保持しています。ここでメッセージ形式を変更した場合は、その言語を使用しているすべての同梱コピーに変更を反映してください - それらを結び付けるビルドステップやパッケージレジストリは存在しません。
