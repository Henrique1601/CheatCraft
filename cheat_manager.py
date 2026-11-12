import time
import threading
from typing import Dict, Any, Callable
from memory_engine import MemoryEngine

class CheatManager:
    """
    Manages active cheats, background freeze loops, and cheat logic.
    """
    def __init__(self, memory_engine: MemoryEngine):
        self.mem = memory_engine
        self.running = False
        self.loop_thread: threading.Thread = None
        
        # Cheat status dictionary
        self.cheats: Dict[str, Dict[str, Any]] = {
            "god_mode": {
                "name": "God Mode (Vida Infinita)",
                "active": False,
                "type": "freeze_float",
                "value": 1000.0,
                "base_offset": 0x0,
                "offsets": [0x0],
                "description": "Mantém a vida de Peter Parker no valor máximo"
            },
            "infinite_focus": {
                "name": "Foco Infinito / Finalizadores",
                "active": False,
                "type": "freeze_float",
                "value": 100.0,
                "base_offset": 0x0,
                "offsets": [0x0],
                "description": "Barra de foco 100% cheia para curas instantâneas e finalizadores"
            },
            "infinite_gadgets": {
                "name": "Munição de Gadgets Infinita",
                "active": False,
                "type": "freeze_int",
                "value": 99,
                "base_offset": 0x0,
                "offsets": [0x0],
                "description": "Teias, bombas de teia e dispositivos nunca se esgotam"
            },
            "max_combo": {
                "name": "Multiplicador de Combo Máximo",
                "active": False,
                "type": "freeze_int",
                "value": 999,
                "base_offset": 0x0,
                "offsets": [0x0],
                "description": "Mantém o contador de combos no ápice para EXP rápida"
            },
            "infinite_tokens": {
                "name": "Fichas / Pontos de Habilidade",
                "active": False,
                "type": "set_int",
                "value": 9999,
                "base_offset": 0x0,
                "offsets": [0x0],
                "description": "Define fichas de base, pesquisa, marcos e pontos de skill"
            },
            "speedhack": {
                "name": "Super Velocidade (Speedhack)",
                "active": False,
                "type": "freeze_float",
                "value": 2.5,
                "base_offset": 0x0,
                "offsets": [0x0],
                "description": "Aumenta a velocidade de movimento e balanço de teia"
            }
        }
        
        # Observers to notify UI
        self.on_state_change: Callable[[str, bool], None] = None

    def start_loop(self):
        """Starts background worker thread to enforce active cheats."""
        if self.running:
            return
        self.running = True
        self.loop_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.loop_thread.start()

    def stop_loop(self):
        """Stops background loop."""
        self.running = False

    def toggle_cheat(self, cheat_id: str) -> bool:
        """Toggles a cheat by its ID and returns new state."""
        if cheat_id not in self.cheats:
            return False
            
        cheat = self.cheats[cheat_id]
        cheat["active"] = not cheat["active"]
        
        # If it's a one-time set cheat
        if cheat["active"] and cheat["type"] == "set_int":
            self._apply_single_write(cheat)
            cheat["active"] = False # Auto toggle off after applying
            
        if self.on_state_change:
            self.on_state_change(cheat_id, cheat["active"])
            
        return cheat["active"]

    def _apply_single_write(self, cheat: Dict[str, Any]):
        """Executes a single value assignment."""
        if not self.mem.is_connected:
            return
        addr = self.mem.resolve_pointer(cheat["base_offset"], cheat["offsets"])
        if addr and addr > 0:
            self.mem.write_int(addr, int(cheat["value"]))

    def _worker_loop(self):
        """Continuously freezes values in memory for active cheats."""
        while self.running:
            if self.mem.is_connected:
                for cheat_id, cheat in self.cheats.items():
                    if not cheat["active"]:
                        continue

                    addr = self.mem.resolve_pointer(cheat["base_offset"], cheat["offsets"])
                    if not addr or addr == 0:
                        continue

                    if cheat["type"] == "freeze_float":
                        self.mem.write_float(addr, float(cheat["value"]))
                    elif cheat["type"] == "freeze_int":
                        self.mem.write_int(addr, int(cheat["value"]))

            time.sleep(0.05) # 20 Hz update loop (suave e sem sobrecarga de CPU)
