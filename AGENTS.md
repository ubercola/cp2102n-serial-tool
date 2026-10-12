# Agent guidance

Read `docs/PROTOCOL.md` and `docs/SOURCES.md` before modifying USB or config
code.

CP2102N configuration is OTP:

- use full-block GetConfig/SetConfig, never legacy SetSerialNumber;
- never retry writes automatically;
- reject locked, unknown-version, or unexpected-size configurations;
- preserve bytes outside the serial area and checksum;
- verify the complete block after writing;
- never set the lock byte or program multiple devices automatically;
- do not perform physical USB writes without explicit user approval.

Run the unit tests after every behavior change:

```bash
./.venv/bin/python -m unittest discover -s tests -v
```
