import winsound
import time
from typing import Optional, Callable

class SoundFeedback:
    """
    Emite feedbacks sonoros nativos e sutis do Windows para eventos do CheatCraft
    (Ativação de Cheat, Conexão com Jogo, Desconexão) sem dependências externas.
    """
    @staticmethod
    def play_connected():
        """Dois beeps ascendentes indicando jogo detectado e conectado."""
        try:
            winsound.Beep(587, 80) # D5
            winsound.Beep(880, 100) # A5
        except Exception:
            pass

    @staticmethod
    def play_cheat_on():
        """Beep curto e agudo indicando cheat ativado."""
        try:
            winsound.Beep(1046, 70) # C6
        except Exception:
            pass

    @staticmethod
    def play_cheat_off():
        """Beep grave indicando cheat desativado."""
        try:
            winsound.Beep(440, 70) # A4
        except Exception:
            pass

    @staticmethod
    def play_disconnected():
        """Beep descendente indicando que o jogo foi encerrado."""
        try:
            winsound.Beep(440, 80)
            winsound.Beep(330, 100)
        except Exception:
            pass
