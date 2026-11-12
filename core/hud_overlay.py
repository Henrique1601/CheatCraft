import tkinter as tk
import time
import ctypes
from typing import Dict, Any, Callable
import keyboard

class InGameHUDOverlay:
    """
    Overlay transparente gamer com:
    - Lista de Cheats ativos em tempo real
    - Contador de FPS (taxa de atualização por delta-time)
    - Mira Virtual Customizável (Crosshair) para jogos sem mira com click-through Win32
    - Tecla global [Insert] para alternar visibilidade com segurança de threads
    - Janela arrastável via clique e arraste do mouse
    """
    def __init__(self, title: str = "CheatCraft HUD"):
        self.title = title
        self.root = None
        self.visible = False
        self.cheat_labels = {}
        self.status_label = None
        self.fps_label = None
        self.items_container = None
        self.cross_btn = None

        # Drag tracking
        self._drag_start_x = 0
        self._drag_start_y = 0

        # Crosshair Window
        self.crosshair_window = None
        self.crosshair_enabled = False
        self.crosshair_color = "#00ffcc" # Ciano gamer

        # FPS metrics
        self.last_time = time.time()
        self.frame_count = 0
        self.current_fps = 60
        self._fps_timer_id = None

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

        # Suporte a clique-e-arraste (Draggable HUD)
        def start_drag(event):
            self._drag_start_x = event.x
            self._drag_start_y = event.y

        def do_drag(event):
            x = self.root.winfo_x() + (event.x - self._drag_start_x)
            y = self.root.winfo_y() + (event.y - self._drag_start_y)
            self.root.geometry(f"+{x}+{y}")

        frame.bind("<Button-1>", start_drag)
        frame.bind("<B1-Motion>", do_drag)

        # Header
        head = tk.Label(frame, text="⚡ CHEATCRAFT HUD PRO", fg="#00d2ff", bg="#12121f", font=("Segoe UI", 11, "bold"), cursor="fleur")
        head.pack(pady=(8, 1))
        head.bind("<Button-1>", start_drag)
        head.bind("<B1-Motion>", do_drag)

        sub = tk.Label(frame, text="[INSERT] Ocultar / Exibir (Arraste para mover)", fg="#7a7a99", bg="#12121f", font=("Segoe UI", 8), cursor="fleur")
        sub.pack(pady=(0, 4))
        sub.bind("<Button-1>", start_drag)
        sub.bind("<B1-Motion>", do_drag)

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
        """Calcula taxa de frames/refresh rate do overlay de forma segura na thread da UI."""
        if not self.root:
            return
        try:
            if not self.root.winfo_exists():
                return
        except Exception:
            return

        now = time.time()
        self.frame_count += 1
        delta = now - self.last_time
        if delta >= 0.5:
            self.current_fps = int(self.frame_count / delta)
            if self.fps_label:
                try:
                    self.fps_label.configure(text=f"FPS: {self.current_fps}")
                except Exception:
                    pass
            self.frame_count = 0
            self.last_time = now

        try:
            self._fps_timer_id = self.root.after(16, self._fps_updater)
        except Exception:
            self._fps_timer_id = None

    def destroy(self):
        """Fecha o HUD e limpa recursos de forma limpa."""
        if self._fps_timer_id and self.root:
            try:
                self.root.after_cancel(self._fps_timer_id)
            except Exception:
                pass
            self._fps_timer_id = None
        if self.crosshair_window:
            try:
                self.crosshair_window.destroy()
            except Exception:
                pass
            self.crosshair_window = None
        if self.root:
            try:
                self.root.destroy()
            except Exception:
                pass
            self.root = None

    def toggle_crosshair(self):
        """Cria ou oculta mira centralizada sobre a tela inteira (Thread-Safe)."""
        if not self.root:
            return

        def _do_toggle():
            self.crosshair_enabled = not self.crosshair_enabled
            if self.crosshair_enabled:
                if not self.crosshair_window:
                    self._create_crosshair_window()
                else:
                    self.crosshair_window.deiconify()
                if self.cross_btn:
                    self.cross_btn.configure(text="🎯 Mira Virtual: ATIVA", bg="#008066", fg="#00ffcc")
            else:
                if self.crosshair_window:
                    self.crosshair_window.withdraw()
                if self.cross_btn:
                    self.cross_btn.configure(text="🎯 Mira Virtual: OFF", bg="#2c2c44", fg="#ffffff")

        self.root.after(0, _do_toggle)

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

        self.crosshair_window.update()

        # Aplica estilos Win32 para Click-Through total (WS_EX_TRANSPARENT | WS_EX_LAYERED | WS_EX_NOACTIVATE)
        try:
            user32 = ctypes.windll.user32
            hwnd = user32.GetParent(self.crosshair_window.winfo_id()) or self.crosshair_window.winfo_id()
            GWL_EXSTYLE = -20
            WS_EX_TRANSPARENT = 0x00000020
            WS_EX_LAYERED = 0x00080000
            WS_EX_NOACTIVATE = 0x08000000
            current_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            user32.SetWindowLongW(hwnd, GWL_EXSTYLE, current_style | WS_EX_TRANSPARENT | WS_EX_LAYERED | WS_EX_NOACTIVATE)
        except Exception as e:
            print(f"Aviso: falha ao aplicar estilos click-through na mira: {e}")

    def update_cheats(self, cheats: Dict[str, bool]):
        """Atualiza a lista de cheats exibida no HUD de forma thread-safe."""
        if not self.root:
            return

        def _do_update():
            if not self.items_container:
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

        self.root.after(0, _do_update)

    def toggle_visibility(self):
        """Alterna a exibição da janela do HUD sem ocultar a mira se ela estiver ativa (Thread-Safe)."""
        if not self.root:
            return

        def _do_toggle():
            self.visible = not self.visible
            if self.visible:
                self.root.deiconify()
            else:
                self.root.withdraw()
                # Garante que a mira permaneça visível mesmo com o HUD oculto
                if self.crosshair_enabled and self.crosshair_window:
                    self.crosshair_window.deiconify()

        self.root.after(0, _do_toggle)
