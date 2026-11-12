from typing import List, Dict, Any, Optional

class EmulatorManager:
    """
    Gerencia suporte e mapeamento de memória para os principais emuladores de console.
    """
    EMULATOR_PROFILES = {
        "rpcs3.exe": {
            "name": "RPCS3 (PlayStation 3)",
            "base_memory": "0x100000000",
            "endianness": "big",
            "type": "PS3"
        },
        "pcsx2.exe": {
            "name": "PCSX2 (PlayStation 2)",
            "base_memory": "0x20000000",
            "endianness": "little",
            "type": "PS2"
        },
        "pcsx2-qtx64.exe": {
            "name": "PCSX2 Qt (PlayStation 2)",
            "base_memory": "0x20000000",
            "endianness": "little",
            "type": "PS2"
        },
        "Dolphin.exe": {
            "name": "Dolphin (GameCube / Wii)",
            "base_memory": "0x80000000",
            "endianness": "big",
            "type": "GameCube/Wii"
        },
        "Cemu.exe": {
            "name": "Cemu (Wii U)",
            "base_memory": "0x10000000",
            "endianness": "big",
            "type": "WiiU"
        }
    }

    @classmethod
    def is_emulator(cls, process_name: str) -> bool:
        return process_name in cls.EMULATOR_PROFILES

    @classmethod
    def get_profile(cls, process_name: str) -> Optional[Dict[str, Any]]:
        return cls.EMULATOR_PROFILES.get(process_name)

    @classmethod
    def translate_console_address(cls, process_name: str, console_address: int, emulator_base_ptr: int) -> int:
        """
        Converte um endereço nativo do console para o endereço virtual alocado no processo do PC.
        """
        profile = cls.get_profile(process_name)
        if not profile:
            return console_address

        # Cálculo do offset relativo dentro do bloco de memória virtual do console
        virtual_base = int(profile["base_memory"], 16)
        offset = console_address - virtual_base
        return emulator_base_ptr + offset
