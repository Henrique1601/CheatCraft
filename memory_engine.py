import os
import re
import time
import ctypes
import logging
from typing import Optional, List, Union, Dict
import pymem
import pymem.process
import pymem.pattern

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s - %(message)s")

class MemoryEngine:
    """
    Robust memory reading, writing, pointer resolution and pattern scanning engine.
    Supports 32-bit and 64-bit processes, universal address and module string parsing,
    leak-free process connection caching, and pointer chain walking.
    """
    def __init__(self, process_name: str = "spiderman.exe"):
        self.process_name = process_name
        self.pm: Optional[pymem.Pymem] = None
        self.base_address: int = 0
        self.is_connected: bool = False
        self._connected_process_name: str = ""
        self._module_cache: Dict[str, int] = {}

    @property
    def is_64_bit(self) -> bool:
        """Determines if the hooked process is 64-bit (x64) or 32-bit (x86/WoW64)."""
        if not self.is_connected or not self.pm or not self.pm.process_handle:
            return True
        try:
            return pymem.process.is_64_bit(self.pm.process_handle)
        except Exception:
            return True

    def connect(self) -> bool:
        """
        Attempt to hook into target process and retrieve base module.
        Validates existing process handle before re-hooking to prevent Win32 handle leaks.
        """
        if not self.process_name:
            self.disconnect()
            return False

        # If already connected to the same process, verify the handle is still valid
        if self.is_connected and self.pm and self.pm.process_handle:
            if getattr(self, "_connected_process_name", "").lower() == self.process_name.lower():
                exit_code = ctypes.c_ulong()
                # STILL_ACTIVE = 259
                if ctypes.windll.kernel32.GetExitCodeProcess(self.pm.process_handle, ctypes.byref(exit_code)):
                    if exit_code.value == 259:
                        return True

        # Process changed, died, or not yet connected - cleanly disconnect old handles first
        self.disconnect()

        try:
            self.pm = pymem.Pymem(self.process_name)
            module = pymem.process.module_from_name(self.pm.process_handle, self.process_name)
            if module:
                self.base_address = module.lpBaseOfDll
                self.is_connected = True
                self._connected_process_name = self.process_name
                self._module_cache[self.process_name.lower()] = self.base_address
                logging.info(f"Connected to {self.process_name} (PID: {self.pm.process_id}, Base: 0x{self.base_address:X})")
                return True
            else:
                self.disconnect()
        except Exception:
            self.disconnect()
        return False

    def disconnect(self):
        """Detach cleanly from the process and close open handles."""
        self.is_connected = False
        if self.pm:
            try:
                self.pm.close_process()
            except Exception:
                pass
            self.pm = None
        self.base_address = 0
        self._connected_process_name = ""
        self._module_cache.clear()

    def get_module_base(self, module_name: str) -> Optional[int]:
        """
        Retrieves the base address of a loaded module (e.g. 'GTA5.exe', 'UnityPlayer.dll').
        Uses internal caching to avoid redundant module enumeration calls.
        """
        if not self.is_connected:
            return None

        clean_name = module_name.strip('"\'').lower()
        if clean_name in self._module_cache:
            return self._module_cache[clean_name]

        # Fallback: if matches current process name and base_address is known
        if clean_name == self.process_name.lower() and self.base_address > 0:
            self._module_cache[clean_name] = self.base_address
            return self.base_address

        if self.pm and self.pm.process_handle:
            try:
                mod = pymem.process.module_from_name(self.pm.process_handle, clean_name)
                if mod:
                    self._module_cache[clean_name] = mod.lpBaseOfDll
                    return mod.lpBaseOfDll
            except Exception:
                pass

        return None

    def parse_address(self, address: Union[str, int]) -> Optional[int]:
        """
        Universal address parser for:
        - Module strings with offset: '"GTA5.exe"+01C3A100', '"UnityPlayer.dll"+015F3C00', 'game.exe+0x1000'
        - Raw hex strings: '0x140001000', '140001000'
        - Integers: 0x140001000
        """
        if isinstance(address, int):
            return address
        if not isinstance(address, str):
            return None

        addr_str = address.strip()
        if not addr_str:
            return None

        # Pattern: "module.ext"+offset or module.ext+offset (with + or -)
        m = re.match(r'^(?:"([^"]+)"|([a-zA-Z0-9_\.\-]+))\s*([+-])\s*(0x[0-9a-fA-F]+|[0-9a-fA-F]+)$', addr_str)
        if m:
            mod_name = m.group(1) or m.group(2)
            sign = m.group(3)
            raw_off = m.group(4)
            try:
                offset = int(raw_off, 16)
            except ValueError:
                try:
                    offset = int(raw_off, 0)
                except ValueError:
                    return None

            base = self.get_module_base(mod_name)
            if base is None:
                return None
            return (base + offset) if sign == '+' else (base - offset)

        # Standalone module name: "GTA5.exe" or UnityPlayer.dll
        clean_name = addr_str.strip('"\'')
        if clean_name.lower().endswith(('.exe', '.dll')):
            return self.get_module_base(clean_name)

        # Direct hex / decimal address string
        try:
            if addr_str.lower().startswith("0x"):
                return int(addr_str, 16)
            return int(addr_str, 16)
        except ValueError:
            try:
                return int(addr_str, 10)
            except ValueError:
                return None

    def resolve_pointer(self, base: Union[str, int], offsets: Optional[List[int]] = None) -> Optional[int]:
        """
        Resolves multi-level 64-bit or 32-bit pointer chains.
        Supports both module address strings ('"GTA5.exe"+01C3A100') and raw base offsets.
        Example: [[base_address + base_offset] + off1] + off2 ...
        """
        if not self.is_connected:
            return None

        if isinstance(base, str):
            current_addr = self.parse_address(base)
            if current_addr is None:
                return None
        elif isinstance(base, int):
            if base == 0:
                current_addr = self.base_address
            elif self.base_address > 0 and base < self.base_address and base < 0x10000000:
                # Relative base offset
                current_addr = self.base_address + base
            else:
                # Absolute integer address
                current_addr = base
        else:
            return None

        if not offsets:
            return current_addr

        if not self.pm:
            return None

        try:
            # Walk through pointer chain
            for offset in offsets[:-1]:
                if self.is_64_bit:
                    current_addr = self.pm.read_longlong(current_addr)
                else:
                    current_addr = self.pm.read_int(current_addr)

                if not current_addr or current_addr <= 0:
                    return None
                current_addr += offset

            if self.is_64_bit:
                final_addr = self.pm.read_longlong(current_addr)
            else:
                final_addr = self.pm.read_int(current_addr)

            if not final_addr or final_addr <= 0:
                return None
            return final_addr + offsets[-1]
        except Exception:
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

    def read_double(self, address: int) -> Optional[float]:
        if not self.is_connected or not self.pm:
            return None
        try:
            return self.pm.read_double(address)
        except Exception:
            return None

    def write_double(self, address: int, value: float) -> bool:
        if not self.is_connected or not self.pm:
            return False
        try:
            self.pm.write_double(address, float(value))
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
