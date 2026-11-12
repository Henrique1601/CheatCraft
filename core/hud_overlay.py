import tkinter as tk
import time
from typing import Dict, Any, Callable
import keyboard

class InGameHUDOverlay:
    """
    Overlay transparente gamer com:
    - Lista de Cheats ativos em tempo real
    - Contador de FPS (taxa de atualização por delta-time)
    - Mira Virtual Customizável (Crosshair) para jogos sem mira
    - Tecla global [Insert] para alternar visibilidade
    """
    def __init__(self, title: str = "CheatCraft HUD"):
        self.title = title
        self.root = None
        self.visible = False
        self.cheat_labels = {}
        self.status_label = None
        self.fps_label = None

        # Crosshair Window
        self.crosshair_window = None
        self.crosshair_enabled = False
        self.crosshair_color = "#00ffcc" # Ciano gamer

        # FPS metrics
        self.last_time = time.time()
        self.frame_count = 0
        self.current_fps = 60

    def create_window(self):
        if self.root:
            return

        self.root = tk.Tk()
        self.root.title(self.title)
        self.root.geometry("290x380+30+30")
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        self.root.wm_attributes("-alpha", 0.88)
        self.root.configure(bg="#0a0a12")

        # Container Principal com Borda Neon
        frame = tk.Frame(self.root, bg="#12121f", highlightbackground="#00d2ff", highlightthickness=1)
        frame.pack(fill="both", expand=True, padx=2, pady=2)

        # Header
        head = tk.Label(frame, text="⚡ CHEATCRAFT HUD PRO", fg="#00d2ff", bg="#12121f", font=("Segoe UI", 11, "bold"))
        head.pack(pady=(8, 1))

        sub = tk.Label(frame, text="[INSERT] Ocultar / Exibir", fg="#7a7a99", bg="#12121f", font=("Segoe UI", 8))
        sub.pack(pady=(0, 4))

        # Status & FPS Bar
        metrics_bar = tk.Frame(frame, bg="#12121f")
        metrics_bar.pack(fill="x", padx=12, pady=(0, 6))

        self.status_label = tk.Label(metrics_bar, text="● Conectado", fg="#00ff66", bg="#12121f", font=("Segoe UI", 9, "bold"))
        self.status_label.pack(side="left")

        self.fps_label = tk.Label(metrics_bar, text="FPS: 60", fg="#ffcc00", bg="#12121f", font=("Consolas", 9, "bold"))
        self.fps_label.pack(side="right")

        # Seção Cheats
        cheats_title = tk.Label(frame, text="MODIFICADORES ATIVOS:", fg="#9999bb", bg="#12121f", font=("Segoe UI", 8, "bold"), anchor="w")
        cheats_title.pack(fill="x", padx=12, pady=(4, 2))

        self.items_container = tk.Frame(frame, bg="#12121f")
        self.items_container.pack(fill="both", expand=True, padx=12)

        # Barra Inferior Gamer: Mira Customizada
        footer = tk.Frame(frame, bg="#181829")
        footer.pack(fill="x", side="bottom", padx=4, pady=4)

        self.cross_btn = tk.Button(
            footer,
            text="🎯 Mira Virtual: OFF",
            fg="#ffffff",
            bg="#2c2c44",
            activebackground="#3d3d5c",
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            command=self.toggle_crosshair
        )
        self.cross_btn.pack(fill="x", padx=6, pady=4)

        # Loop de atualização de FPS
        self._fps_updater()

        try:
            keyboard.add_hotkey("insert", self.toggle_visibility, suppress=False)
        except Exception:
            pass

    def _fps_updater(self):
        """Calcula taxa de frames/refresh rate do overlay."""
        now = time.time()
        self.frame_count += 1
        delta = now - self.last_time
        if delta >= 0.5:
            self.current_fps = int(self.frame_count / delta)
            if self.fps_label:
                self.fps_label.configure(text=f"FPS: {self.current_fps}")
            self.frame_count = 0
            self.last_time = now

        if self.root:
            self.root.after(16, self._fps_updater)

    def toggle_crosshair(self):
        """Cria ou oculta mira centralizada sobre a tela inteira."""
        self.crosshair_enabled = not self.crosshair_enabled
        if self.crosshair_enabled:
            if not self.crosshair_window:
                self._create_crosshair_window()
            else:
                self.crosshair_window.deiconify()
            self.cross_btn.configure(text="🎯 Mira Virtual: ATIVA", bg="#008066", fg="#00ffcc")
        else:
            if self.crosshair_window:
                self.crosshair_window.withdraw()
            self.cross_btn.configure(text="🎯 Mira Virtual: OFF", bg="#2c2c44", fg="#ffffff")

    def _create_crosshair_window(self):
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        size = 24
        x = (screen_w // 2) - (size // 2)
        y = (screen_h // 2) - (size // 2)

        self.crosshair_window = tk.Toplevel(self.root)
        self.crosshair_window.geometry(f"{size}x{size}+{x}+{y}")
        self.crosshair_window.overrideredirect(True)
        self.crosshair_window.wm_attributes("-topmost", True)
        self.crosshair_window.wm_attributes("-transparentcolor", "#000001")
        self.crosshair_window.configure(bg="#000001")

        canvas = tk.Canvas(self.crosshair_window, width=size, height=size, bg="#000001", highlightthickness=0)
        canvas.pack()

        # Desenha mira em cruz moderna com ponto central
        c_x, c_y = size // 2, size // 2
        # Linha vertical
        canvas.create_line(c_x, 2, c_x, size - 2, fill=self.crosshair_color, width=2)
        # Linha horizontal
        canvas.create_line(2, c_y, size - 2, c_y, fill=self.crosshair_color, width=2)
        # Ponto central
        canvas.create_oval(c_x - 1, c_y - 1, c_x + 1, c_y + 1, fill="#ffffff", outline="#ffffff")

    def update_cheats(self, cheats: Dict[str, bool]):
        if not self.root:
            return

        for widget in self.items_container.winfo_children():
            widget.destroy()

        for name, active in cheats.items():
            row = tk.Frame(self.items_container, bg="#12121f")
            row.pack(fill="x", pady=2)

            lbl = tk.Label(row, text=name, fg="#ffffff", bg="#12121f", font=("Segoe UI", 9), anchor="w")
            lbl.pack(side="left")

            state_lbl = tk.Label(
                row,
                text="ATIVO" if active else "OFF",
                fg="#00ff66" if active else "#666688",
                bg="#12121f",
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
