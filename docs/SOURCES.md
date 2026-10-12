# Technical sources

The implementation was derived from Silicon Labs' public CP210x
documentation and the CP210xManufacturing source package supplied with the
original project.

## Public documentation

- [AN721: USBXpress Device Configuration and Programming Guide](https://www.silabs.com/documents/public/application-notes/AN721.pdf)
- [AN976: CP2101/2/3/4/9 to CP2102N Porting Guide](https://www.silabs.com/documents/public/application-notes/an976-cp2102-3-4-9-to-cp2102n-porting-guide.pdf)

AN976 is especially important: individual legacy configuration API calls,
including `CP210x_SetSerialNumber`, must be replaced with
`CP210x_GetConfig`/`CP210x_SetConfig` for CP2102N.

## Original source references

These paths refer to the source tree from which this standalone project was
extracted. The proprietary source files are not redistributed here.

- `srcpkg/cp210xmanufacturing/cp210xmanufacturing/src/CP2102NDevice.cpp`
  — GetConfig and SetConfig USB control transfers.
- `srcpkg/cp210xmanufacturing/cp210xmanufacturing/src/CP210xDevice.cpp`
  — part-number request and reset behavior.
- `srcpkg/cp210xsmt/cp210xsmt.cpp`
  — CP2102N config layout, USB string encoding, lock check and checksum
  placement.
- `srcpkg/cp210xsmt/util.cpp`
  — Fletcher-16 implementation.
- `include/CP210xManufacturingDLL.h`
  — API status values and public limits.

When updating protocol constants, verify them against a current Silicon Labs
document or source release and update `docs/PROTOCOL.md` and tests together.
