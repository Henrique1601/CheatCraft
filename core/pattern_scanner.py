import re
from typing import Optional, List, Tuple
import pymem
import pymem.process
import pymem.pattern

class PatternScanner:
    """
    Motor de varredura por assinaturas AOB (Array of Bytes com wildcards '??' ou '?').
    Encontra endereços de funções e variáveis mesmo após o jogo receber updates e patches.
    """

    @staticmethod
    def parse_aob_string(aob_str: str) -> Tuple[bytes, str]:
        """
        Converte string AOB estilo Cheat Engine (ex: '48 89 5C 24 ?? 57 48 83 EC 20')
        em uma tupla (bytes_pattern, mask).
        """
        tokens = aob_str.strip().split()
        pattern_bytes = bytearray()
        mask_chars = []

        for t in tokens:
            t = t.strip()
            if t in ["?", "??"]:
                pattern_bytes.append(0)
                mask_chars.append("?")
            else:
                pattern_bytes.append(int(t, 16))
                mask_chars.append("x")

        return bytes(pattern_bytes), "".join(mask_chars)

    @classmethod
    def scan_module_aob(cls, pm: pymem.Pymem, module_name: str, aob_str: str) -> Optional[int]:
        """
        Varre o módulo especificado procurando a assinatura AOB.
        Retorna o endereço de memória absoluto do primeiro match ou None.
        """
        if not pm or not pm.process_handle:
            return None

        try:
            module = pymem.process.module_from_name(pm.process_handle, module_name)
            if not module:
                return None

            # Converte formato
            pattern, mask = cls.parse_aob_string(aob_str)

            # Executa scan via pymem.pattern
            return pymem.pattern.pattern_scan_module(pm.process_handle, module, pattern)
        except Exception as e:
            print(f"Erro no AOB Scan: {e}")
            return None
