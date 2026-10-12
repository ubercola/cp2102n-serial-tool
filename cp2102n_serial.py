#!/usr/bin/env python3

import sys

import usb.core
import usb.util


SILABS_VID = 0x10C4
USB_TIMEOUT_MS = 7000

CP2102N_PART_NUMBERS = (0x20, 0x21, 0x22)
PART_NAMES = {
    0x01: "CP2101",
    0x02: "CP2102",
    0x03: "CP2103",
    0x04: "CP2104",
    0x05: "CP2105",
    0x08: "CP2108",
    0x09: "CP2109",
    0x20: "CP2102N QFN28",
    0x21: "CP2102N QFN24",
    0x22: "CP2102N QFN20",
}

MAX_SERIAL_LENGTH = 63
CP2102N_CONFIG_SIZE = 678
CP2102N_CONFIG_VERSION = 1
CP2102N_CONFIG_UNLOCKED = 0xFF
CP2102N_SERIAL_OFFSET = 55 + 4 + 131 + 259
CP2102N_SERIAL_SIZE = 131
CP2102N_CHECKSUM_SIZE = 2


class ToolError(Exception):
    pass


def control_read(device, value, length):
    try:
        data = device.ctrl_transfer(
            0xC0,
            0xFF,
            value,
            0,
            length,
            timeout=USB_TIMEOUT_MS,
        )
    except usb.core.USBError as error:
        raise ToolError("USB read failed: %s" % error) from error

    if len(data) != length:
        raise ToolError(
            "USB read returned %d bytes instead of %d" % (len(data), length)
        )
    return bytes(data)


def control_write(device, value, data):
    try:
        written = device.ctrl_transfer(
            0x40,
            0xFF,
            value,
            0,
            data,
            timeout=USB_TIMEOUT_MS,
        )
    except usb.core.USBError as error:
        raise ToolError("USB write failed: %s" % error) from error

    if written != len(data):
        raise ToolError(
            "USB write accepted %d bytes instead of %d"
            % (written, len(data))
        )


def get_part_number(device):
    return control_read(device, 0x370B, 1)[0]


def get_serial(device):
    try:
        return device.serial_number or "<empty>"
    except (ValueError, usb.core.USBError):
        return "<unavailable>"


def get_config(device):
    size_data = control_read(device, 0x000E, 2)
    size = size_data[0] | (size_data[1] << 8)
    if size <= 2:
        raise ToolError("Device returned an invalid config size: %d" % size)
    return control_read(device, 0x000E, size)


def set_config(device, config):
    control_write(device, 0x370F, config)


def fletcher16(data):
    sum1 = 0xFF
    sum2 = 0xFF
    offset = 0
    remaining = len(data)

    while remaining:
        block_length = min(remaining, 20)
        remaining -= block_length
        for value in data[offset : offset + block_length]:
            sum1 += value
            sum2 += sum1
        offset += block_length
        sum1 = (sum1 & 0xFF) + (sum1 >> 8)
        sum2 = (sum2 & 0xFF) + (sum2 >> 8)

    sum1 = (sum1 & 0xFF) + (sum1 >> 8)
    sum2 = (sum2 & 0xFF) + (sum2 >> 8)
    return (sum2 << 8) | sum1


def set_serial_in_config(config_data, serial):
    config = bytearray(config_data)

    if len(config) != CP2102N_CONFIG_SIZE:
        raise ToolError(
            "Unsupported CP2102N config size: %d (expected %d)"
            % (len(config), CP2102N_CONFIG_SIZE)
        )

    stored_size = config[0] | (config[1] << 8)
    if stored_size != len(config):
        raise ToolError("Invalid CP2102N config size field: %d" % stored_size)

    if config[2] != CP2102N_CONFIG_VERSION:
        raise ToolError(
            "Unsupported CP2102N config version: %d" % config[2]
        )

    if config[4] != CP2102N_CONFIG_UNLOCKED:
        raise ToolError("CP2102N configuration is locked and cannot be changed")

    serial_utf16 = serial.encode("utf-16le")
    descriptor_length = len(serial_utf16) + 2
    start = CP2102N_SERIAL_OFFSET
    end = start + CP2102N_SERIAL_SIZE

    config[start:end] = b"\x00" * CP2102N_SERIAL_SIZE
    config[start] = 0
    config[start + 1] = descriptor_length
    config[start + 2] = 0x03
    config[start + 3 : start + 3 + len(serial_utf16)] = serial_utf16

    checksum = fletcher16(config[:-CP2102N_CHECKSUM_SIZE])
    config[-2] = (checksum >> 8) & 0xFF
    config[-1] = checksum & 0xFF
    return bytes(config)


def discover_devices():
    try:
        candidates = usb.core.find(find_all=True, idVendor=SILABS_VID)
    except usb.core.NoBackendError as error:
        raise ToolError(
            "libusb backend was not found; see README.md"
        ) from error

    devices = []
    for device in candidates:
        try:
            part_number = get_part_number(device)
        except ToolError:
            usb.util.dispose_resources(device)
            continue

        if part_number not in PART_NAMES:
            usb.util.dispose_resources(device)
            continue

        devices.append(
            {
                "device": device,
                "part_number": part_number,
                "serial": get_serial(device),
            }
        )
    return devices


def select_device(devices):
    print("Available CP210x devices:")
    for index, info in enumerate(devices):
        part_number = info["part_number"]
        support = (
            "supported"
            if part_number in CP2102N_PART_NUMBERS
            else "unsupported"
        )
        print(
            "[%d] %s (part 0x%02X), SERIAL_NUMBER: %s [%s]"
            % (
                index,
                PART_NAMES[part_number],
                part_number,
                info["serial"],
                support,
            )
        )

    try:
        selection = input("Select device index: ")
        index = int(selection)
    except (EOFError, KeyboardInterrupt):
        raise ToolError("Input cancelled")
    except ValueError:
        raise ToolError("Device index must be an integer")

    if index < 0 or index >= len(devices):
        raise ToolError(
            "Device index must be between 0 and %d" % (len(devices) - 1)
        )

    info = devices[index]
    if info["part_number"] not in CP2102N_PART_NUMBERS:
        raise ToolError("The selected device is not a supported CP2102N")
    return info


def read_new_serial():
    try:
        serial = input("Enter new SERIAL_NUMBER: ")
    except (EOFError, KeyboardInterrupt):
        raise ToolError("Input cancelled")

    if not serial:
        raise ToolError("SERIAL_NUMBER must not be empty")

    try:
        serial.encode("ascii")
    except UnicodeEncodeError:
        raise ToolError("SERIAL_NUMBER must contain ASCII characters only")

    if len(serial) > MAX_SERIAL_LENGTH:
        raise ToolError(
            "SERIAL_NUMBER is too long: maximum is %d characters"
            % MAX_SERIAL_LENGTH
        )
    return serial


def program_serial(device, serial):
    current_config = get_config(device)
    new_config = set_serial_in_config(current_config, serial)
    set_config(device, new_config)

    programmed_config = get_config(device)
    if programmed_config != new_config:
        raise ToolError("Verification failed: configuration readback differs")

    print("New SERIAL_NUMBER: %s" % serial)
    print("Resetting device")
    try:
        device.reset()
    except usb.core.USBError as error:
        # A reset after changing USB descriptors can make the device
        # re-enumerate before libusb finishes the request. In that case the
        # old USB address no longer exists, which is a successful outcome.
        if error.errno in (2, 19) or getattr(
            error, "backend_error_code", None
        ) in (-4, -5):
            print("Device disconnected for USB re-enumeration")
            return
        raise ToolError("Device reset failed: %s" % error) from error


def main():
    devices = []
    try:
        devices = discover_devices()
        if not devices:
            raise ToolError(
                "No accessible CP210x devices found; see README.md"
            )

        selected = select_device(devices)
        print("Current SERIAL_NUMBER: %s" % selected["serial"])
        serial = read_new_serial()
        program_serial(selected["device"], serial)
        print("Done. Reconnect the device if the serial does not refresh.")
        return 0
    except ToolError as error:
        print("Error: %s" % error, file=sys.stderr)
        return 1
    finally:
        for info in devices:
            usb.util.dispose_resources(info["device"])


if __name__ == "__main__":
    sys.exit(main())
