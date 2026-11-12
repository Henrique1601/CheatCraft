import ctypes
import struct
from typing import List, Dict, Any, Optional
import pymem
import pymem.ressources.kernel32

# Constantes do Windows API
PAGE_READWRITE = 0x04
PAGE_EXECUTE_READWRITE = 0x40
MEM_COMMIT = 0x1000

class MemoryScanner:
    """
    Scanner nativo de memória de processo para busca e isolamento de valores
    (First Scan, Next Scan) suportando Inteiros (4 Bytes) e Floats.
    """
    def __init__(self, pm: Optional[pymem.Pymem] = None):
        self.pm = pm
        self.found_addresses: List[int] = []

    def set_process(self, pm: pymem.Pymem):
        self.pm = pm
        self.found_addresses.clear()

    def first_scan(self, value: Any, val_type: str = "4 Bytes", max_results: int = 10000) -> List[int]:
        """
        Executa First Scan em todas as regiões comitadas e com permissão de escrita.
        """
        self.found_addresses.clear()
        if not self.pm or not self.pm.process_handle:
            return []

        results = []
        try:
            # Converte valor para bytes
            if val_type == "4 Bytes":
                target_bytes = struct.pack("<i", int(value))
            elif val_type == "Float":
                target_bytes = struct.pack("<f", float(value))
            else:
                target_bytes = struct.pack("<i", int(value))

            # Varredura de páginas de memória do processo
            current_addr = 0x10000 # Começa após região nula
            max_addr = 0x7FFFFFFFFFFF # Limite de espaço de usuário em 64-bit

            while current_addr < max_addr and len(results) < max_results:
                mbi = pymem.ressources.structure.MEMORY_BASIC_INFORMATION()
                mbi_size = ctypes.sizeof(mbi)
                success = pymem.ressources.kernel32.VirtualQueryEx(
                    self.pm.process_handle,
                    ctypes.c_void_p(current_addr),
                    ctypes.byref(mbi),
                    mbi_size
                )
                if not success:
                    break

                # Filtra apenas memória alocada e com permissão de escrita
                if mbi.State == MEM_COMMIT and (mbi.Protect & (PAGE_READWRITE | PAGE_EXECUTE_READWRITE)):
                    try:
                        region_bytes = self.pm.read_bytes(mbi.BaseAddress, mbi.RegionSize)
                        offset = 0
                        while True:
                            idx = region_bytes.find(target_bytes, offset)
                            if idx == -1:
                                break
                            results.append(mbi.BaseAddress + idx)
                            if len(results) >= max_results:
                                break
                            offset = idx + 1
                    except Exception:
                        pass

                current_addr = mbi.BaseAddress + mbi.RegionSize

        except Exception as e:
            print(f"Erro no First Scan: {e}")

        self.found_addresses = results
        return self.found_addresses

    def next_scan(self, value: Any, val_type: str = "4 Bytes") -> List[int]:
        """
        Filtra os endereços salvos na lista anterior para o novo valor informado.
        """
        if not self.pm or not self.found_addresses:
            return []

        filtered = []
        for addr in self.found_addresses:
            try:
                if val_type == "4 Bytes":
                    cur_val = self.pm.read_int(addr)
                    if cur_val == int(value):
                        filtered.append(addr)
                elif val_type == "Float":
                    cur_val = self.pm.read_float(addr)
                    if abs(cur_val - float(value)) < 0.01:
                        filtered.append(addr)
            except Exception:
                continue

        self.found_addresses = filtered
        return self.found_addresses
