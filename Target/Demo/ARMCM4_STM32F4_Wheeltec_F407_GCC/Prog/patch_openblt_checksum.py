#!/usr/bin/env python3
"""Patch the OpenBLT application checksum into the ELF image."""

from __future__ import annotations

import struct
import subprocess
import sys
import tempfile
from pathlib import Path


CHECKSUM_OFFSET = 0x1AC
VECTOR_WORD_COUNT = 7


def main() -> int:
  if len(sys.argv) != 2:
    print("usage: patch_openblt_checksum.py <elf>", file=sys.stderr)
    return 1

  elf_path = Path(sys.argv[1]).resolve()
  objcopy = "arm-none-eabi-objcopy"

  with tempfile.TemporaryDirectory() as temp_dir:
    vector_path = Path(temp_dir) / "isr_vector.bin"
    subprocess.check_call([objcopy, f"--dump-section", f".isr_vector={vector_path}", str(elf_path)])

    vector_data = bytearray(vector_path.read_bytes())
    if len(vector_data) < CHECKSUM_OFFSET + 4:
      raise RuntimeError(".isr_vector section is smaller than the OpenBLT checksum offset")

    checksum = 0
    for offset in range(0, VECTOR_WORD_COUNT * 4, 4):
      checksum = (checksum + struct.unpack_from("<I", vector_data, offset)[0]) & 0xFFFFFFFF
    checksum = (~checksum + 1) & 0xFFFFFFFF
    struct.pack_into("<I", vector_data, CHECKSUM_OFFSET, checksum)
    vector_path.write_bytes(vector_data)

    subprocess.check_call([objcopy, "--update-section", f".isr_vector={vector_path}", str(elf_path)])

  return 0


if __name__ == "__main__":
  raise SystemExit(main())
