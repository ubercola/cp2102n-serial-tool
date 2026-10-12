# CP2102N Serial Number Tool

[English](README.md) | [Русский](README_ru.md)

A portable interactive tool for changing the USB `SERIAL_NUMBER` of a
CP2102N on Linux. It lists available CP210x devices, lets the user select a
CP2102N, writes a new serial number, and verifies the configuration by
reading it back.

The tool uses PyUSB/libusb and does not require
`libcp210xmanufacturing.so`.

## Supported devices

- CP2102N QFN28 (`part number 0x20`)
- CP2102N QFN24 (`part number 0x21`)
- CP2102N QFN20 (`part number 0x22`)

Other CP210x devices appear in the list, but the tool will not program them.

## System requirements

- Linux x86_64
- Python 3.8 or newer
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

## Transfer and installation

Copy the entire `cp2102n-serial-tool` directory to the target machine.
Do not transfer an existing `.venv` directory between machines.

```bash
cd cp2102n-serial-tool
chmod +x setup.sh run.sh install-udev-rule.sh
./setup.sh
sudo ./install-udev-rule.sh
```

After installing the udev rule, unplug and reconnect the device. The rule
grants local users access to all Silicon Labs USB devices with VID `10c4`.
If these permissions are too broad for your environment, restrict the rule
to a specific PID or group.

## Running

```bash
./run.sh
```

Example:

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

The new serial number must:

- contain between 1 and 63 ASCII characters;
- be unique among USB devices used at the same time.

## How programming works

CP2102N does not support the legacy `CP210x_SetSerialNumber` call. The tool
reads the complete configuration block with `GetConfig`, updates the serial
number USB string descriptor, recalculates the Fletcher-16 checksum, writes
the complete block with `SetConfig`, and reads it back for verification.

All other configuration parameters remain unchanged.

## Important limitations

CP2102N uses OTP configuration. Do not perform unnecessary test writes. If
the configuration is already locked (`enableConfigUpdate != 0xff`), the
serial number cannot be changed and the tool will stop before writing.

Do not disconnect power while programming. The tool does not remove or set
the configuration lock.

## Troubleshooting

`No accessible CP210x devices found`

- reconnect the device after installing the udev rule;
- check the USB cable;
- confirm that the device appears in `lsusb`;
- for diagnostics, try `sudo ./run.sh` once.

`libusb backend was not found`

- install the system libusb 1.0 package.

`CP2102N configuration is locked`

- the device configuration is permanently protected from changes and cannot
  be unlocked in software.

`USB write failed`

- check the udev permissions and USB connection;
- make sure a CP2102N device is selected;
- do not repeatedly retry the write if the error persists.

During reset, the device disconnects from its old USB address and
re-enumerates. `Errno 2` and `Errno 19` at this stage are treated as an
expected result.

## Development

Before changing USB commands or the configuration structure, read:

- `docs/PROTOCOL.md` — commands, offsets, serial format, and checksum;
- `docs/SOURCES.md` — documentation and protocol sources;
- `AGENTS.md` — mandatory safety rules for coding agents.

Run the tests:

```bash
./.venv/bin/python -m unittest discover -s tests -v
```

## Project contents

- `cp2102n_serial.py` — application;
- `requirements.txt` — Python dependencies;
- `vendor/` — bundled PyUSB package for offline installation;
- `setup.sh` — virtual environment setup;
- `run.sh` — launcher;
- `install-udev-rule.sh` — USB permission rule installer;
- `udev/99-cp210x.rules` — Silicon Labs USB access rule;
- `docs/` — protocol documentation and source references;
- `tests/` — unit tests that do not access USB;
- `AGENTS.md` and `.cursor/rules/` — coding-agent instructions.
