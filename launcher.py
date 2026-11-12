import os
import json
import threading
import time
import customtkinter as ctk
from tkinter import filedialog, messagebox

from core.ct_generator import CheatTableGenerator
from core.game_scanner import GameScanner
from memory_engine import MemoryEngine

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class CheatCraftApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("⚡ CheatCraft // Launcher, Modder & .CT Generator")
        self.geometry("980x680")
        self.minsize(880, 600)

        # Estados e Dados
        self.presets = self._load_presets()
        self.selected_game = self.presets[0] if self.presets else None
        self.detected_games = []
        self.mem = MemoryEngine(process_name=self.selected_game["process_name"] if self.selected_game else "")
        self.active_cheats = {}

        self._build_layout()
        self._start_steam_scan_async()
        self._start_process_monitor_async()

    def _load_presets(self):
        presets_path = os.path.join(os.path.dirname(__file__), "templates", "presets.json")
        if os.path.exists(presets_path):
            try:
                with open(presets_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("presets", [])
            except Exception as e:
                print(f"Erro ao carregar presets: {e}")
        return []

    def _build_layout(self):
        # Grid Principal: Sidebar Esquerda + Conteúdo Direita
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ------------------- SIDEBAR ESQUERDA -------------------
        sidebar = ctk.CTkFrame(self, width=280, corner_radius=0, fg_color=("#161622", "#0f0f18"))
        sidebar.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        sidebar.grid_propagate(False)

        # Logo / Título
        logo_lbl = ctk.CTkLabel(
            sidebar,
            text="⚡ CheatCraft",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#00d2ff"
        )
        logo_lbl.pack(pady=(20, 4), padx=20, anchor="w")

        sub_logo = ctk.CTkLabel(
            sidebar,
            text="Universal Game Modder & .CT Studio",
            font=ctk.CTkFont(size=11),
            text_color="#7b7b99"
        )
        sub_logo.pack(pady=(0, 20), padx=20, anchor="w")

        # Seção Jogos & Presets
        sec_title = ctk.CTkLabel(
            sidebar,
            text="BIBLIOTECA DE JOGOS",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#9090b0"
        )
        sec_title.pack(padx=20, pady=(10, 5), anchor="w")

        self.games_scroll = ctk.CTkScrollableFrame(sidebar, fg_color="transparent")
        self.games_scroll.pack(fill="both", expand=True, padx=10, pady=5)
        self._render_game_list()

        # Botão Escanear Steam
        scan_btn = ctk.CTkButton(
            sidebar,
            text="🔄 Detectar Jogos Steam",
            fg_color="#222238",
            hover_color="#31314f",
            command=self._manual_steam_scan
        )
        scan_btn.pack(padx=20, pady=(10, 20), fill="x")

        # ------------------- CONTEÚDO PRINCIPAL (DIREITA) -------------------
        main_content = ctk.CTkFrame(self, fg_color=("#1d1d2b", "#141420"), corner_radius=0)
        main_content.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        main_content.grid_columnconfigure(0, weight=1)
        main_content.grid_rowconfigure(2, weight=1)

        # Top Bar: Status do Jogo Selecionado
        top_bar = ctk.CTkFrame(main_content, fg_color=("#242436", "#1c1c2b"), corner_radius=12)
        top_bar.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))

        self.game_header_title = ctk.CTkLabel(
            top_bar,
            text=self.selected_game["game_name"] if self.selected_game else "Selecione um Jogo",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#ffffff"
        )
        self.game_header_title.pack(side="left", padx=16, pady=12)

        # Indicador de Processo Ativo
        self.status_badge = ctk.CTkLabel(
            top_bar,
            text="● Desconectado",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#ff5555"
        )
        self.status_badge.pack(side="right", padx=16, pady=12)

        # Ações Rápidas (Barra de Ferramentas)
        actions_bar = ctk.CTkFrame(main_content, fg_color="transparent")
        actions_bar.grid(row=1, column=0, sticky="ew", padx=20, pady=5)

        export_ct_btn = ctk.CTkButton(
            actions_bar,
            text="📄 Gerar Tabela .CT (Cheat Engine)",
            fg_color="#0080ff",
            hover_color="#0066cc",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._export_cheat_table
        )
        export_ct_btn.pack(side="left", padx=(0, 10))

        add_custom_btn = ctk.CTkButton(
            actions_bar,
            text="➕ Adicionar Cheat Personalizado",
            fg_color="#2c2c40",
            hover_color="#3a3a55",
            command=self._open_add_cheat_modal
        )
        add_custom_btn.pack(side="left")

        # Lista de Cheats do Jogo
        self.cheats_container = ctk.CTkScrollableFrame(
            main_content,
            label_text="MODIFICADORES DE MEMÓRIA & CHEATS ATIVOS",
            fg_color=("#181826", "#11111c")
        )
        self.cheats_container.grid(row=2, column=0, sticky="nsew", padx=20, pady=(5, 20))
        self._render_cheats_list()

    def _render_game_list(self):
        for widget in self.games_scroll.winfo_children():
            widget.destroy()

        for g in self.presets:
            is_active = self.selected_game and self.selected_game.get("id") == g.get("id")
            btn = ctk.CTkButton(
                self.games_scroll,
                text=f"🎮 {g['game_name']}",
                anchor="w",
                fg_color="#0066cc" if is_active else "transparent",
                hover_color="#1f2d4d" if not is_active else "#0055aa",
                font=ctk.CTkFont(size=12, weight="bold" if is_active else "normal"),
                command=lambda item=g: self._select_game(item)
            )
            btn.pack(fill="x", pady=2)

    def _select_game(self, game_dict):
        self.selected_game = game_dict
        self.mem.process_name = game_dict.get("process_name", "")
        self.game_header_title.configure(text=game_dict["game_name"])
        self._render_game_list()
        self._render_cheats_list()

    def _render_cheats_list(self):
        for widget in self.cheats_container.winfo_children():
            widget.destroy()

        if not self.selected_game or not self.selected_game.get("cheats"):
            empty_lbl = ctk.CTkLabel(
                self.cheats_container,
                text="Nenhum cheat configurado para este jogo ainda.",
                text_color="#6e6e8a"
            )
            empty_lbl.pack(pady=40)
            return

        for cheat in self.selected_game["cheats"]:
            card = ctk.CTkFrame(self.cheats_container, corner_radius=10, fg_color=("#232336", "#1a1a29"))
            card.pack(fill="x", pady=6, padx=4)

            info_box = ctk.CTkFrame(card, fg_color="transparent")
            info_box.pack(side="left", fill="both", expand=True, padx=14, pady=10)

            title = ctk.CTkLabel(
                info_box,
                text=cheat["description"],
                font=ctk.CTkFont(size=14, weight="bold"),
                anchor="w"
            )
            title.pack(fill="x")

            offsets_str = ", ".join([hex(o) for o in cheat.get("offsets", [])])
            details = ctk.CTkLabel(
                info_box,
                text=f"Tipo: {cheat.get('type')}  |  Endereço: {cheat.get('address')}  |  Offsets: [{offsets_str}]  |  Hotkey: [{cheat.get('hotkey', 'Nenhum')}]",
                font=ctk.CTkFont(size=11),
                text_color="#8f8fa8",
                anchor="w"
            )
            details.pack(fill="x")

            switch = ctk.CTkSwitch(
                card,
                text="",
                progress_color="#00d2ff",
                command=lambda cid=cheat["id"]: self._toggle_live_cheat(cid)
            )
            switch.pack(side="right", padx=16)

    def _toggle_live_cheat(self, cheat_id):
        curr = self.active_cheats.get(cheat_id, False)
        self.active_cheats[cheat_id] = not curr

    def _export_cheat_table(self):
        if not self.selected_game:
            return

        default_filename = f"{self.selected_game.get('id', 'game')}_table.ct"
        initial_dir = os.path.join(os.path.dirname(__file__), "exports")
        
        file_path = filedialog.asksaveasfilename(
            initialdir=initial_dir,
            initialfile=default_filename,
            defaultextension=".ct",
            filetypes=[("Cheat Engine Table", "*.ct"), ("Todos os Arquivos", "*.*")]
        )

        if file_path:
            try:
                CheatTableGenerator.generate_ct(
                    game_title=self.selected_game["game_name"],
                    process_name=self.selected_game["process_name"],
                    entries=self.selected_game["cheats"],
                    output_path=file_path
                )
                messagebox.showinfo(
                    "Tabela .CT Gerada com Sucesso!",
                    f"A tabela do Cheat Engine foi criada com sucesso:\n\n{file_path}\n\nVocê já pode abri-la diretamente no Cheat Engine!"
                )
            except Exception as e:
                messagebox.showerror("Erro ao Gerar Tabela", f"Falha: {e}")

    def _open_add_cheat_modal(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Adicionar Novo Cheat / Modificador")
        modal.geometry("460x420")
        modal.resizable(False, False)

        ctk.CTkLabel(modal, text="Nome / Descrição:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20, pady=(15, 2))
        desc_entry = ctk.CTkEntry(modal, placeholder_text="Ex: Munição Infinita")
        desc_entry.pack(fill="x", padx=20)

        ctk.CTkLabel(modal, text="Tipo de Dado:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20, pady=(10, 2))
        type_combo = ctk.CTkComboBox(modal, values=["4 Bytes", "Float", "Double", "Binary", "Auto Assembler Script"])
        type_combo.pack(fill="x", padx=20)

        ctk.CTkLabel(modal, text="Endereço / Módulo Base:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20, pady=(10, 2))
        addr_entry = ctk.CTkEntry(modal, placeholder_text='Ex: "game.exe"+01A2B3C0')
        addr_entry.pack(fill="x", padx=20)

        ctk.CTkLabel(modal, text="Offsets (separados por vírgula):", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20, pady=(10, 2))
        offsets_entry = ctk.CTkEntry(modal, placeholder_text="Ex: 0x48, 0x10, 0x0")
        offsets_entry.pack(fill="x", padx=20)

        def save_cheat():
            desc = desc_entry.get().strip()
            if not desc:
                return

            offsets_raw = offsets_entry.get().strip()
            parsed_offsets = []
            if offsets_raw:
                for off in offsets_raw.split(","):
                    off_clean = off.strip()
                    try:
                        parsed_offsets.append(int(off_clean, 16) if "0x" in off_clean.lower() else int(off_clean))
                    except ValueError:
                        pass

            new_c = {
                "id": f"custom_{int(time.time())}",
                "description": desc,
                "type": type_combo.get(),
                "address": addr_entry.get().strip() or f'"{self.selected_game["process_name"]}"+0',
                "offsets": parsed_offsets,
                "hotkey": "None"
            }

            self.selected_game["cheats"].append(new_c)
            self._render_cheats_list()
            modal.destroy()

        save_btn = ctk.CTkButton(modal, text="💾 Salvar Cheat", fg_color="#00a86b", hover_color="#008f5a", command=save_cheat)
        save_btn.pack(pady=20, padx=20, fill="x")

    def _manual_steam_scan(self):
        threading.Thread(target=self._run_steam_scan, daemon=True).start()

    def _start_steam_scan_async(self):
        threading.Thread(target=self._run_steam_scan, daemon=True).start()

    def _run_steam_scan(self):
        detected = GameScanner.scan_installed_games()
        if detected:
            for d in detected:
                # Evita duplicatas se já estiver na lista
                if not any(p["process_name"].lower() == d["executable"].lower() for p in self.presets):
                    self.presets.append({
                        "id": d["name"].lower().replace(" ", "_"),
                        "game_name": f"{d['name']} ({d['engine_type']})",
                        "process_name": d["executable"],
                        "cheats": [
                            {
                                "id": "god_mode",
                                "description": "God Mode (Auto-Generated)",
                                "type": "Float",
                                "address": f'"{d["executable"]}"+0',
                                "offsets": [0],
                                "hotkey": "NUMPAD 1"
                            }
                        ]
                    })
            self.after(0, self._render_game_list)

    def _start_process_monitor_async(self):
        def monitor():
            while True:
                if self.selected_game and self.selected_game.get("process_name"):
                    proc_name = self.selected_game["process_name"]
                    self.mem.process_name = proc_name
                    connected = self.mem.connect()
                    if connected:
                        self.after(0, lambda: self.status_badge.configure(
                            text=f"● Conectado ({proc_name})", text_color="#00ff66"
                        ))
                    else:
                        self.after(0, lambda: self.status_badge.configure(
                            text=f"● Desconectado ({proc_name})", text_color="#ff5555"
                        ))
                time.sleep(2.0)

        threading.Thread(target=monitor, daemon=True).start()

if __name__ == "__main__":
    app = CheatCraftApp()
    app.mainloop()
