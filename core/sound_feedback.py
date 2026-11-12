import winsound
import threading
from typing import Optional, Callable

class SoundFeedback:
    """
    Emite feedbacks sonoros nativos e sutis do Windows para eventos do CheatCraft
    (Ativação de Cheat, Conexão com Jogo, Desconexão) sem dependências externas,
    executando de forma 100% assíncrona para não travar a interface gráfica.
    """
    @staticmethod
    def _run_async(target_func: Callable):
        t = threading.Thread(target=target_func, daemon=True)
        t.start()

    @classmethod
    def play_connected(cls):
        """Dois beeps ascendentes indicando jogo detectado e conectado."""
        def _beep():
            try:
                winsound.Beep(587, 80) # D5
                winsound.Beep(880, 100) # A5
            except Exception:
                pass
        cls._run_async(_beep)

    @classmethod
    def play_cheat_on(cls):
        """Beep curto e agudo indicando cheat ativado."""
        def _beep():
            try:
                winsound.Beep(1046, 70) # C6
            except Exception:
                pass
        cls._run_async(_beep)

    @classmethod
    def play_cheat_off(cls):
        """Beep grave indicando cheat desativado."""
        def _beep():
            try:
                winsound.Beep(440, 70) # A4
            except Exception:
                pass
        cls._run_async(_beep)

    @classmethod
    def play_disconnected(cls):
        """Beep descendente indicando que o jogo foi encerrado."""
        def _beep():
            try:
                winsound.Beep(440, 80)
                winsound.Beep(330, 100)
            except Exception:
                pass
        cls._run_async(_beep)
