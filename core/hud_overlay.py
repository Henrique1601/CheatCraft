import tkinter as tk
from typing import Dict, Any, Callable
import keyboard

class InGameHUDOverlay:
    """
    Overlay transparente flutuante (Topmost) que fica sobreposto à tela do jogo.
    Pode ser alternado com a tecla 'Insert'.
    """
    def __init__(self, title: str = "CheatCraft HUD"):
        self.title = title
        self.root = None
        self.visible = False
        self.cheat_labels = {}
        self.status_label = None

    def create_window(self):
        if self.root:
            return

        self.root = tk.Tk()
        self.root.title(self.title)
        self.root.geometry("280x320+30+30")
        self.root.overrideredirect(True) # Remove barra de título
        self.root.wm_attributes("-topmost", True) # Sempre visível sobre o jogo
        self.root.wm_attributes("-alpha", 0.85) # Semi-transparência moderna
        self.root.configure(bg="#0c0c14")

        # Container Principal com Borda
        frame = tk.Frame(self.root, bg="#141422", highlightbackground="#00d2ff", highlightthickness=1)
        frame.pack(fill="both", expand=True, padx=2, pady=2)

        # Header
        head = tk.Label(frame, text="⚡ CHEATCRAFT HUD", fg="#00d2ff", bg="#141422", font=("Segoe UI", 11, "bold"))
        head.pack(pady=(8, 2))

        sub = tk.Label(frame, text="[INSERT] Ocultar / Exibir", fg="#7a7a99", bg="#141422", font=("Segoe UI", 8))
        sub.pack(pady=(0, 6))

        self.status_label = tk.Label(frame, text="● Conectado ao Jogo", fg="#00ff66", bg="#141422", font=("Segoe UI", 9, "bold"))
        self.status_label.pack(pady=(0, 8))

        self.items_container = tk.Frame(frame, bg="#141422")
        self.items_container.pack(fill="both", expand=True, padx=10)

        # Atalho Global para Alternar HUD
        try:
            keyboard.add_hotkey("insert", self.toggle_visibility, suppress=False)
        except Exception:
            pass

    def update_cheats(self, cheats: Dict[str, bool]):
        if not self.root:
            return

        for widget in self.items_container.winfo_children():
            widget.destroy()

        for name, active in cheats.items():
            row = tk.Frame(self.items_container, bg="#141422")
            row.pack(fill="x", pady=2)

            lbl = tk.Label(row, text=name, fg="#ffffff", bg="#141422", font=("Segoe UI", 9), anchor="w")
            lbl.pack(side="left")

            state_lbl = tk.Label(
                row,
                text="ATIVO" if active else "OFF",
                fg="#00ff66" if active else "#666688",
                bg="#141422",
                font=("Segoe UI", 8, "bold")
            )
            state_lbl.pack(side="right")

    def toggle_visibility(self):
        if not self.root:
            return
        self.visible = not self.visible
        if self.visible:
            self.root.deiconify()
        else:
            self.root.withdraw()
