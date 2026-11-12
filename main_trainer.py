import os
import sys
import time
import threading
import configparser
import customtkinter as ctk
import keyboard
from memory_engine import MemoryEngine
from cheat_manager import CheatManager

# Set visual appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class SpiderManTrainerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Marvel's Spider-Man Remastered // TRAINER PRO")
        self.geometry("640 x 720")
        self.minsize(580, 650)
        self.resizable(False, False)

        # Core Engines
        self.config_path = os.path.join(os.path.dirname(__file__), "config.ini")
        self.mem = MemoryEngine(process_name="spiderman.exe")
        self.manager = CheatManager(self.mem)
        self.manager.start_loop()

        # State mapping
        self.switches = {}
        self.hotkeys = {
            "god_mode": "num 1",
            "infinite_focus": "num 2",
            "infinite_gadgets": "num 3",
            "max_combo": "num 4",
            "infinite_tokens": "num 5",
            "speedhack": "num 6",
        }

        # Build UI & Listeners
        self._build_ui()
        self._setup_hotkeys()
        self._start_process_watcher()

    def _build_ui(self):
        # Header Frame
        header = ctk.CTkFrame(self, corner_radius=12, fg_color=("#1f1f2e", "#14141f"))
        header.pack(fill="x", padx=20, pady=(20, 10))

        title_label = ctk.CTkLabel(
            header,
            text="🕷️ SPIDER-MAN PRO TRAINER",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#e50914"
        )
        title_label.pack(pady=(12, 2))

        sub_label = ctk.CTkLabel(
            header,
            text="Universal Memory Hook & Modifier | v1.0.0",
            font=ctk.CTkFont(size=12),
            text_color="#8888aa"
        )
        sub_label.pack(pady=(0, 10))

        # Status Bar
        self.status_frame = ctk.CTkFrame(self, corner_radius=8, fg_color=("#2a2020", "#241818"))
        self.status_frame.pack(fill="x", padx=20, pady=5)

        self.status_indicator = ctk.CTkLabel(
            self.status_frame,
            text="●",
            text_color="#ff4444",
            font=ctk.CTkFont(size=16)
        )
        self.status_indicator.pack(side="left", padx=(15, 5), pady=8)

        self.status_text = ctk.CTkLabel(
            self.status_frame,
            text="Aguardando inicialização do jogo (spiderman.exe)...",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#ff8888"
        )
        self.status_text.pack(side="left", pady=8)

        # Cheats Container Card
        cards_frame = ctk.CTkScrollableFrame(self, label_text="CHEATS DISPONÍVEIS & ATALHOS")
        cards_frame.pack(fill="both", expand=True, padx=20, pady=10)

        for cheat_id, cheat in self.manager.cheats.items():
            card = ctk.CTkFrame(cards_frame, corner_radius=10, fg_color=("#262638", "#1c1c28"))
            card.pack(fill="x", pady=6, padx=4)

            # Left Info
            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True, padx=12, pady=10)

            title = ctk.CTkLabel(
                info_frame,
                text=cheat["name"],
                font=ctk.CTkFont(size=14, weight="bold"),
                anchor="w"
            )
            title.pack(fill="x")

            desc = ctk.CTkLabel(
                info_frame,
                text=f"{cheat['description']}  |  Hotkey: [{self.hotkeys.get(cheat_id, 'None')}]",
                font=ctk.CTkFont(size=11),
                text_color="#a0a0b8",
                anchor="w"
            )
            desc.pack(fill="x")

            # Right Switch
            switch = ctk.CTkSwitch(
                card,
                text="",
                command=lambda cid=cheat_id: self._on_switch_toggled(cid),
                onvalue=True,
                offvalue=False,
                progress_color="#e50914"
            )
            switch.pack(side="right", padx=15)
            self.switches[cheat_id] = switch

        # Footer Actions
        footer = ctk.CTkFrame(self, corner_radius=10, fg_color="transparent")
        footer.pack(fill="x", padx=20, pady=(5, 15))

        offsets_btn = ctk.CTkButton(
            footer,
            text="⚙️ Abrir Config (Offsets/Pointers)",
            fg_color="#33334d",
            hover_color="#444466",
            command=self._open_config_file
        )
        offsets_btn.pack(side="left", padx=(0, 10))

        help_btn = ctk.CTkButton(
            footer,
            text="📖 Guia de Offsets",
            fg_color="#33334d",
            hover_color="#444466",
            command=self._show_help_dialog
        )
        help_btn.pack(side="left")

    def _on_switch_toggled(self, cheat_id: str):
        active = self.switches[cheat_id].get()
        # Sync with manager
        self.manager.cheats[cheat_id]["active"] = active
        if active and self.manager.cheats[cheat_id]["type"] == "set_int":
            self.manager._apply_single_write(self.manager.cheats[cheat_id])
            # Auto switch off in UI for single writes
            self.after(300, lambda: self.switches[cheat_id].deselect())

    def _setup_hotkeys(self):
        """Bind global keyboard shortcuts even when game is focused."""
        def make_handler(cid):
            return lambda: self.after(0, lambda: self._toggle_by_hotkey(cid))

        for cheat_id, hotkey in self.hotkeys.items():
            try:
                keyboard.add_hotkey(hotkey, make_handler(cheat_id), suppress=False)
            except Exception as e:
                print(f"Erro ao registrar hotkey {hotkey}: {e}")

    def _toggle_by_hotkey(self, cheat_id: str):
        if cheat_id in self.switches:
            switch = self.switches[cheat_id]
            if switch.get():
                switch.deselect()
            else:
                switch.select()
            self._on_switch_toggled(cheat_id)

    def _start_process_watcher(self):
        """Runs in background thread to monitor game process attach/detach."""
        def watcher():
            while True:
                connected = self.mem.connect()
                if connected:
                    self.after(0, self._set_status_connected)
                else:
                    self.after(0, self._set_status_disconnected)
                time.sleep(2.0)

        t = threading.Thread(target=watcher, daemon=True)
        t.start()

    def _set_status_connected(self):
        self.status_frame.configure(fg_color=("#182a18", "#122012"))
        self.status_indicator.configure(text_color="#00ff66")
        self.status_text.configure(
            text=f"Jogo Detectado: spiderman.exe (PID: {self.mem.pm.process_id if self.mem.pm else 'OK'})",
            text_color="#88ff88"
        )

    def _set_status_disconnected(self):
        self.status_frame.configure(fg_color=("#2a2020", "#241818"))
        self.status_indicator.configure(text_color="#ff4444")
        self.status_text.configure(
            text="Aguardando inicialização do jogo (spiderman.exe)...",
            text_color="#ff8888"
        )

    def _open_config_file(self):
        if os.path.exists(self.config_path):
            os.system(f'notepad "{self.config_path}"')

    def _show_help_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Como configurar Offsets e Ponteiros")
        dialog.geometry("500x380")
        dialog.resizable(False, False)

        txt = (
            "COMO FUNCIONA O TRAINER:\n\n"
            "1. Abra o jogo 'spiderman.exe'. O Trainer detectará automaticamente.\n"
            "2. As Hotkeys (Num 1 até Num 6) funcionam dentro do jogo sem precisar dar Alt+Tab.\n"
            "3. Se você usar Cheat Engine para achar endereços estáticos ou ponteiros multiníveis:\n"
            "   - Abra o botão 'Abrir Config (Offsets/Pointers)'.\n"
            "   - Coloque o Base Offset (ex: 0x01B4D200) e os Offsets (ex: 0x48,0x10,0x28).\n"
            "   - O Trainer atualizará dinamicamente o valor na memória congelando a cada 50ms.\n"
            "4. Divirta-se!"
        )
        lbl = ctk.CTkLabel(dialog, text=txt, justify="left", wraplength=460, font=ctk.CTkFont(size=12))
        lbl.pack(padx=20, pady=20)


if __name__ == "__main__":
    app = SpiderManTrainerApp()
    app.mainloop()
