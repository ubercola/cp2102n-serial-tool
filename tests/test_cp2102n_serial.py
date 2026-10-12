import unittest
from unittest.mock import patch

import usb.core

import cp2102n_serial as tool


def make_config():
    config = bytearray(tool.CP2102N_CONFIG_SIZE)
    config[0:2] = len(config).to_bytes(2, "little")
    config[2] = tool.CP2102N_CONFIG_VERSION
    config[4] = tool.CP2102N_CONFIG_UNLOCKED
    return config


class ConfigTests(unittest.TestCase):
    def test_fletcher16_known_vector(self):
        self.assertEqual(tool.fletcher16(bytes(range(32))), 0x65F1)

    def test_serial_descriptor_and_checksum(self):
        original = make_config()
        result = tool.set_serial_in_config(original, "0015")
        offset = tool.CP2102N_SERIAL_OFFSET

        self.assertEqual(len(result), tool.CP2102N_CONFIG_SIZE)
        self.assertEqual(result[offset : offset + 3], bytes((0, 10, 3)))
        self.assertEqual(
            result[offset + 3 : offset + 11],
            "0015".encode("utf-16le"),
        )

        checksum = tool.fletcher16(result[:-2])
        self.assertEqual(
            result[-2:],
            bytes((checksum >> 8, checksum & 0xFF)),
        )
        self.assertEqual(result[:offset], bytes(original[:offset]))
        self.assertEqual(
            result[
                offset + tool.CP2102N_SERIAL_SIZE : -2
            ],
            bytes(
                original[
                    offset + tool.CP2102N_SERIAL_SIZE : -2
                ]
            ),
        )

    def test_locked_config_is_rejected(self):
        config = make_config()
        config[4] = 0

        with self.assertRaisesRegex(tool.ToolError, "locked"):
            tool.set_serial_in_config(config, "0015")

    def test_unknown_config_size_is_rejected(self):
        with self.assertRaisesRegex(tool.ToolError, "config size"):
            tool.set_serial_in_config(bytes(32), "0015")


class ResetTests(unittest.TestCase):
    def test_disappearance_during_reset_is_success(self):
        original = make_config()
        programmed = tool.set_serial_in_config(original, "0015")

        class Device:
            def reset(self):
                raise usb.core.USBError("gone", errno=2)

        with patch.object(
            tool, "get_config", side_effect=(bytes(original), programmed)
        ), patch.object(tool, "set_config"):
            tool.program_serial(Device(), "0015")

    def test_unexpected_reset_error_is_reported(self):
        original = make_config()
        programmed = tool.set_serial_in_config(original, "0015")

        class Device:
            def reset(self):
                raise usb.core.USBError("access denied", errno=13)

        with patch.object(
            tool, "get_config", side_effect=(bytes(original), programmed)
        ), patch.object(tool, "set_config"):
            with self.assertRaisesRegex(tool.ToolError, "reset failed"):
                tool.program_serial(Device(), "0015")


if __name__ == "__main__":
    unittest.main()
