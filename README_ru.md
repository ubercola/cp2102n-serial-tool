# CP2102N Serial Number Tool

[English](README.md) | Русский

Переносимый интерактивный инструмент для изменения USB `SERIAL_NUMBER`
у CP2102N под Linux. Он показывает доступные CP210x, позволяет выбрать
нужный CP2102N, записывает новый serial и проверяет конфигурацию чтением.

Инструмент работает через PyUSB/libusb и не требует
`libcp210xmanufacturing.so`.

## Поддерживаемые устройства

- CP2102N QFN28 (`part number 0x20`)
- CP2102N QFN24 (`part number 0x21`)
- CP2102N QFN20 (`part number 0x22`)

Другие CP210x выводятся в списке, но их программирование заблокировано.

## Системные требования

- Linux x86_64
- Python 3.8 или новее
- Python `venv`
- libusb 1.0

Debian/Ubuntu:

```bash
sudo apt update
sudo apt install python3 python3-venv libusb-1.0-0
```

Fedora:

```bash
sudo dnf install python3 libusb1
```

Arch Linux:

```bash
sudo pacman -S python libusb
```

## Перенос и установка

Установка из GitHub:

```bash
git clone https://github.com/ubercola/cp2102n-serial-tool.git
cd cp2102n-serial-tool
chmod +x setup.sh run.sh install-udev-rule.sh
./setup.sh
sudo ./install-udev-rule.sh
```

Альтернативный вариант — скопировать проект вручную:

Скопируйте целиком каталог `cp2102n-serial-tool` на целевую машину.
Текущий каталог `.venv` переносить между машинами не нужно.

```bash
cd cp2102n-serial-tool
chmod +x setup.sh run.sh install-udev-rule.sh
./setup.sh
sudo ./install-udev-rule.sh
```

После установки udev-правила отключите и снова подключите устройство.
Правило предоставляет локальным пользователям доступ ко всем
USB-устройствам Silicon Labs с VID `10c4`. Если это слишком широкие права
для вашей системы, ограничьте правило конкретным PID или группой.

## Запуск

```bash
./run.sh
```

Пример:

```text
Available CP210x devices:
[0] CP2102N QFN28 (part 0x20), SERIAL_NUMBER: 0001 [supported]
Select device index: 0
Current SERIAL_NUMBER: 0001
Enter new SERIAL_NUMBER: 0015
New SERIAL_NUMBER: 0015
Resetting device
Done. Reconnect the device if the serial does not refresh.
```

Новый serial должен:

- содержать от 1 до 63 ASCII-символов;
- быть уникальным среди одновременно используемых USB-устройств.

## Как выполняется запись

CP2102N не поддерживает legacy-вызов `CP210x_SetSerialNumber`.
Инструмент читает полный блок конфигурации командой `GetConfig`, меняет
USB string descriptor серийного номера, пересчитывает Fletcher-16 checksum,
пишет полный блок через `SetConfig` и читает его обратно для проверки.

Остальные параметры конфигурации сохраняются без изменений.

## Важные ограничения

CP2102N использует OTP-конфигурацию. Не выполняйте лишние пробные записи.
Если конфигурация уже заблокирована (`enableConfigUpdate != 0xff`), изменить
serial невозможно; инструмент остановится до записи.

Не отключайте питание во время записи. Инструмент не снимает блокировку и
никогда не блокирует конфигурацию самостоятельно.

## Ошибки

`No accessible CP210x devices found`

- переподключите устройство после установки udev-правила;
- проверьте USB-кабель;
- убедитесь, что устройство видно через `lsusb`;
- для диагностики один раз попробуйте `sudo ./run.sh`.

`libusb backend was not found`

- установите системный пакет libusb 1.0.

`CP2102N configuration is locked`

- конфигурация устройства необратимо защищена от изменений; программно
  разблокировать её нельзя.

`USB write failed`

- проверьте права udev и подключение;
- убедитесь, что выбрано устройство CP2102N;
- не повторяйте запись многократно, если ошибка сохраняется.

Во время reset устройство отключается от старого USB-адреса и регистрируется
заново. Ошибки `Errno 2` и `Errno 19` на этом этапе считаются нормальным
результатом переопределения.

## Доработка проекта

Перед изменением USB-команд или структуры конфигурации прочитайте:

- `docs/PROTOCOL.md` — команды, offsets, формат serial и checksum;
- `docs/SOURCES.md` — документация и происхождение протокольных данных;
- `AGENTS.md` — обязательные правила безопасности для агентов.

Запуск тестов:

```bash
./.venv/bin/python -m unittest discover -s tests -v
```

## Состав проекта

- `cp2102n_serial.py` — программа;
- `requirements.txt` — Python-зависимости;
- `vendor/` — локальная копия Python-пакета PyUSB для offline-установки;
- `setup.sh` — создание виртуального окружения;
- `run.sh` — запуск;
- `install-udev-rule.sh` — установка USB-правил;
- `udev/99-cp210x.rules` — правило доступа к Silicon Labs USB.
- `docs/` — описание протокола и ссылки на первоисточники;
- `tests/` — unit-тесты без обращения к USB;
- `AGENTS.md` и `.cursor/rules/` — инструкции для агентов.
