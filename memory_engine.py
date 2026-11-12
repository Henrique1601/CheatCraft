import os
import time
import logging
from typing import Optional, List, Union
import pymem
import pymem.process
import pymem.pattern

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s - %(message)s")

class MemoryEngine:
    """
    Robust memory reading, writing, pointer resolution and pattern scanning engine.
    """
    def __init__(self, process_name: str = "spiderman.exe"):
        self.process_name = process_name
        self.pm: Optional[pymem.Pymem] = None
        self.base_address: int = 0
        self.is_connected: bool = False

    def connect(self) -> bool:
        """Attempt to hook into target process and retrieve base module."""
        try:
            self.pm = pymem.Pymem(self.process_name)
            module = pymem.process.module_from_name(self.pm.process_handle, self.process_name)
            if module:
                self.base_address = module.lpBaseOfDll
                self.is_connected = True
                logging.info(f"Connected to {self.process_name} (PID: {self.pm.process_id}, Base: 0x{self.base_address:X})")
                return True
        except Exception as e:
            self.is_connected = False
            self.pm = None
            self.base_address = 0
        return False

    def disconnect(self):
        """Detach cleanly from the process."""
        self.is_connected = False
        if self.pm:
            try:
                self.pm.close_process()
            except Exception:
                pass
            self.pm = None
            self.base_address = 0

    def resolve_pointer(self, base_offset: int, offsets: List[int]) -> Optional[int]:
        """
        Resolves multi-level 64-bit/32-bit pointer chains.
        Example: [[base_address + base_offset] + off1] + off2 ...
        """
        if not self.is_connected or not self.pm:
            return None

        try:
            current_addr = self.base_address + base_offset
            if not offsets or offsets == [0]:
                return current_addr

            # Walk through pointer chain
            for i, offset in enumerate(offsets[:-1]):
                current_addr = self.pm.read_longlong(current_addr)
                if not current_addr:
                    return None
                current_addr += offset

            final_addr = self.pm.read_longlong(current_addr)
            if not final_addr:
                return None
            return final_addr + offsets[-1]
        except Exception as e:
            # Memory read violation or unallocated address
            return None

    def read_float(self, address: int) -> Optional[float]:
        if not self.is_connected or not self.pm:
            return None
        try:
            return self.pm.read_float(address)
        except Exception:
            return None

    def write_float(self, address: int, value: float) -> bool:
        if not self.is_connected or not self.pm:
            return False
        try:
            self.pm.write_float(address, float(value))
            return True
        except Exception:
            return False

    def read_int(self, address: int) -> Optional[int]:
        if not self.is_connected or not self.pm:
            return None
        try:
            return self.pm.read_int(address)
        except Exception:
            return None

    def write_int(self, address: int, value: int) -> bool:
        if not self.is_connected or not self.pm:
            return False
        try:
            self.pm.write_int(address, int(value))
            return True
        except Exception:
            return False

    def write_bytes(self, address: int, data: bytes) -> bool:
        """Write raw bytes (useful for NOPing instructions like 0x90)."""
        if not self.is_connected or not self.pm:
            return False
        try:
            self.pm.write_bytes(address, data, len(data))
            return True
        except Exception:
            return False

    def aob_scan(self, pattern: bytes) -> Optional[int]:
        """Array of Bytes (AOB) signature scanning."""
        if not self.is_connected or not self.pm:
            return None
        try:
            module = pymem.process.module_from_name(self.pm.process_handle, self.process_name)
            return pymem.pattern.pattern_scan_module(self.pm.process_handle, module, pattern)
        except Exception:
            return None
