import time
from typing import Optional
from memory_engine import MemoryEngine

class SpeedhackController:
    """
    Controlador de velocidade de tempo no jogo. Suporta multiplicadores de 0.25x a 10.0x.
    Trabalha com endereços de time-scale da engine ou simulação de delta-time.
    """
    def __init__(self, mem: MemoryEngine):
        self.mem = mem
        self.current_speed = 1.0
        self.is_enabled = False

    def set_speed(self, multiplier: float, time_scale_addr: Optional[int] = None) -> bool:
        """
        Ajusta o multiplicador de velocidade no jogo.
        Se time_scale_addr for fornecido, escreve diretamente na variável da engine.
        """
        self.current_speed = max(0.1, min(10.0, multiplier))
        self.is_enabled = (self.current_speed != 1.0)

        if time_scale_addr and self.mem and self.mem.is_connected:
            return self.mem.write_float(time_scale_addr, self.current_speed)

        return True

    def reset_speed(self, time_scale_addr: Optional[int] = None) -> bool:
        """Restaura a velocidade normal (1.0x)."""
        return self.set_speed(1.0, time_scale_addr)
