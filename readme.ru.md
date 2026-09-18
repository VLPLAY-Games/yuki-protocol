# Yuki Protocol

Общий протокол обмена сообщениями и SDK для экосистемы Yuki. Каждый модуль (`yuki-core`,
`yuki-webui`, `yuki-device-pc`, `yuki-device-pc-linux`, `yuki-device-android`, `yuki-humidifier`)
использует этот протокол поверх WebSocket - либо подключая этот репозиторий напрямую (в виде
встроенной копии в папке `libs/yuki-protocol/`), либо реализуя протокол на своём собственном
языке.

Текущая версия: **`yuki/1.0`**.

## Реализации

| Язык | Путь | Используется в |
|---|---|---|
| Python | `python/yuki_protocol.py` | `yuki-core`, `yuki-webui`, `yuki-device-pc-linux` |
| C# | `csharp/YukiProtocol.cs` | `yuki-device-pc` |
| JavaScript | `javascript/yuki-protocol.js` | `yuki-webui` (браузер) |
| C++ (ESP32/Arduino) | `esp32/Protocol.h` | `yuki-humidifier` |

Android (`yuki-device-android`) реализует тот же протокол на Kotlin прямо в своём репозитории
(`YukiMessage.kt`/`YukiProtocol.kt`), а не встраивает копию из этого репозитория, поскольку для
Kotlin/Gson пока нет естественного места среди языковых папок этого репозитория.

## Формат сообщений

Каждое сообщение - это один JSON-объект, без бинарного фрейминга и без контрольной суммы:

```json
{
  "protocol": "yuki/1.0",
  "type": "hello",
  "id": "a uuid4 (or device-generated id on ESP32)",
  "timestamp": 1730000000,
  "payload": { "...": "type-specific fields" }
}
```

Типы сообщений покрывают установку соединения (`hello`/`welcome`), статус (`status`/
`extended_status`), команды (`command`/`command_result`, с необязательным циклом подтверждения
`confirm_command`/`confirm_response` для опасных команд), управление устройствами и
аутентификацию (`devices_update`, `device_auth_request`/`device_auth_response`), ротацию токена
(`token_update`, `token_info`, `rotate_token`, ...), метрики (`metrics`, `metrics_request`) и
ретрансляцию сообщений между устройствами (`device_to_device`, `device_response`,
`device_broadcast`). В реализации на JavaScript также есть несколько сообщений-запросов, нужных
только для WebUI (`get_devices`, `get_blacklist`, ...), без которых обходятся остальные языки.

Каждая реализация проставляет и проверяет поле `protocol` как `yuki/1.0` и отклоняет любое другое
значение - согласования версий не предусмотрено, поэтому все модули в одном развёртывании должны
работать с одной и той же мажорной версией протокола.

## Отдельная реализация для ESP32

`esp32/Protocol.h` - эталонная реализация на C++, используемая `yuki-humidifier`. Она только
формирует и отправляет сообщения (`sendStatus`, `sendMetrics`, `sendCommandResult`, ...) - то же
разделение ответственности, что и в остальных языках: диспетчеризация (то есть решение о том, что
означает `command`) находится в приложении, которое использует протокол (`core.py`/
`YukiClient.cs`/собственный `WebSocketHandler.h` увлажнителя), а не в самом слое протокола.
`yuki-humidifier/Protocol.h` - синхронизированная копия этого файла; при редактировании одного из
них не забывайте обновить и другой.

## Синхронизация встроенных копий

`yuki-core/libs/yuki-protocol/`, `yuki-device-pc/libs/yuki-protocol/` и
`yuki-webui/static/libs/yuki-protocol/` - в каждой из них лежит копия соответствующей
языковой папки (папок) из этого репозитория. Когда вы меняете формат сообщений здесь, перенесите
изменение во все встроенные копии, использующие этот язык - никакого шага сборки или реестра
пакетов, который бы связывал их между собой, не существует.
