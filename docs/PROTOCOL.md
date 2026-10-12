# CP2102N protocol notes

This document records the protocol details required to maintain the tool
without the original CP210x source tree.

## USB requests

All vendor requests use `bRequest = 0xff` and `wIndex = 0`.

| Operation | bmRequestType | wValue | Data |
|---|---:|---:|---|
| Read part number | `0xc0` | `0x370b` | 1 byte |
| Read config size | `0xc0` | `0x000e` | 2 bytes, little-endian |
| Read full config | `0xc0` | `0x000e` | `configSize` bytes |
| Write full config | `0x40` | `0x370f` | Complete config block |

Supported CP2102N part numbers are:

- `0x20`: QFN28
- `0x21`: QFN24
- `0x22`: QFN20

Do not use the legacy `CP210x_SetSerialNumber` request (`wValue = 0x3704`)
with CP2102N. CP2102N configuration must be read and written as one block.

## Config block

The supported config version has a total size of 678 bytes:

| Offset | Size | Meaning |
|---:|---:|---|
| 0 | 2 | Config size, little-endian (`678`) |
| 2 | 1 | Config version (`1`) |
| 3 | 1 | Bootloader update flag |
| 4 | 1 | Config update flag; `0xff` means unlocked |
| 5 | 50 | Remaining preamble |
| 55 | 4 | Language descriptor area |
| 59 | 131 | Manufacturer string area |
| 190 | 259 | Product string area |
| 449 | 131 | Serial-number string area |
| 580 | 96 | Remaining configuration |
| 676 | 2 | Fletcher-16 checksum |

The tool must reject unknown sizes and versions. It must also reject writes
when byte 4 is not `0xff`; configuration locking is not reversible.

## Serial-number descriptor

Before writing, clear all 131 bytes starting at offset 449:

| Relative offset | Value |
|---:|---|
| 0 | `0x00`, select custom unpacked UTF-16LE serial |
| 1 | USB descriptor length: UTF-16LE byte count plus 2 |
| 2 | `0x03`, USB string descriptor type |
| 3 | UTF-16LE serial data |

The current tool intentionally accepts only 1–63 ASCII characters even
though the stored representation is UTF-16LE.

## Checksum

Run Fletcher-16 over bytes `0..675`, excluding the final two checksum bytes.
Initialize both sums to `0xff`, reduce every 20 bytes, and perform a final
reduction. Store the result in big-endian order:

- byte 676: high byte;
- byte 677: low byte.

Always read the config back and compare all 678 bytes before reporting
success.

## Reset behavior

After a descriptor change the device can disappear from its old USB address
before `libusb_reset_device` returns. libusb `NO_DEVICE`/`NOT_FOUND`, surfaced
by PyUSB as `Errno 19`/`Errno 2`, is expected after successful verification.
Other reset errors must still be reported.
