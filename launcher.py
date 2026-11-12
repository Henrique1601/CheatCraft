import os
import json
import threading
import time
import keyboard
import customtkinter as ctk
from tkinter import filedialog, messagebox

from core.ct_generator import CheatTableGenerator
from core.ct_importer import CheatTableImporter
from core.game_scanner import GameScanner
from core.memory_scanner import MemoryScanner
from core.hud_overlay import InGameHUDOverlay
from core.cloud_hub import CloudHub
from core.emulator_manager import EmulatorManager
from core.sound_feedback import SoundFeedback
from core.speedhack_controller import SpeedhackController
from core.ai_assistant import AIAssistantEngine
from memory_engine import MemoryEngine

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class CheatCraftApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("⚡ CheatCraft Studio v4.0 Ultimate // Mega Catálogo AAA & Mod Studio")
        self.geometry("1140x760")
        self.minsize(1020, 680)

        # Estados e Dados
        self.presets = self._load_presets()
        self.selected_game = self.presets[0] if self.presets else None
        self.detected_games = []
        self.active_cheats = {}
        self.active_cheat_objects = {}
        self.cheat_switches = {}
        self._registered_hotkeys = []
        self.was_connected = False

        # Módulos do Core v4.0
        self.mem = MemoryEngine(process_name=self.selected_game["process_name"] if self.selected_game else "")
        self.scanner = MemoryScanner()
        self.hud = InGameHUDOverlay()
        self.speedhack = SpeedhackController(self.mem)

        self._build_layout()
        self._setup_game_hotkeys()
        self._start_cheat_enforcement_thread()
        self._start_steam_scan_async()
        self._start_process_monitor_async()

        self._insert_hotkey = None
        try:
            self._insert_hotkey = keyboard.add_hotkey("insert", lambda: self.after(0, self._launch_hud), suppress=False)
        except Exception:
            pass

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

    def _save_presets(self):
        presets_path = os.path.join(os.path.dirname(__file__), "templates", "presets.json")
        try:
            with open(presets_path, "w", encoding="utf-8") as f:
                json.dump({"presets": self.presets}, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar presets: {e}")

    def _build_layout(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ------------------- SIDEBAR ESQUERDA -------------------
        sidebar = ctk.CTkFrame(self, width=310, corner_radius=0, fg_color=("#141422", "#0d0d16"))
        sidebar.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        sidebar.grid_propagate(False)

        logo_lbl = ctk.CTkLabel(
            sidebar,
            text="⚡ CHEATCRAFT",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#00d2ff"
        )
        logo_lbl.pack(pady=(18, 2), padx=20, anchor="w")

        sub_logo = ctk.CTkLabel(
            sidebar,
            text=f"Mega Catálogo AAA ({len(self.presets)} Jogos) & .CT Studio",
            font=ctk.CTkFont(size=11),
            text_color="#7b7b99"
        )
        sub_logo.pack(pady=(0, 12), padx=20, anchor="w")

        # Botão Importar .CT da Internet
        import_btn = ctk.CTkButton(
            sidebar,
            text="📥 Importar Tabela .CT da Web",
            fg_color="#006699",
            hover_color="#0088cc",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._import_external_ct
        )
        import_btn.pack(padx=20, pady=(0, 6), fill="x")

        # Botão Sincronizar Nuvem
        cloud_btn = ctk.CTkButton(
            sidebar,
            text="🌐 Sincronizar Hub Nuvem",
            fg_color="#1d2d44",
            hover_color="#2b4266",
            command=self._sync_cloud
        )
        cloud_btn.pack(padx=20, pady=(0, 8), fill="x")

        # Título da Seção
        sec_title = ctk.CTkLabel(
            sidebar,
            text="CATÁLOGO DE JOGOS & EMULADORES",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#9090b0"
        )
        sec_title.pack(padx=20, pady=(4, 2), anchor="w")

        self.games_scroll = ctk.CTkScrollableFrame(sidebar, fg_color="transparent")
        self.games_scroll.pack(fill="both", expand=True, padx=10, pady=4)
        self._render_game_list()

        # Botão AI Assistant
        ai_btn = ctk.CTkButton(
            sidebar,
            text="🤖 AI Cheat Assistant",
            fg_color="#2d1b4e",
            hover_color="#3e256b",
            command=self._open_ai_assistant_modal
        )
        ai_btn.pack(padx=20, pady=(6, 4), fill="x")

        # Botão In-Game HUD
        hud_btn = ctk.CTkButton(
            sidebar,
            text="🪟 In-Game HUD + FPS (Insert)",
            fg_color="#332244",
            hover_color="#4d3366",
            command=self._launch_hud
        )
        hud_btn.pack(padx=20, pady=(4, 4), fill="x")

        # Botão Escanear Steam
        scan_btn = ctk.CTkButton(
            sidebar,
            text="🔄 Detectar Jogos Locais",
            fg_color="#222238",
            hover_color="#31314f",
            command=self._manual_steam_scan
        )
        scan_btn.pack(padx=20, pady=(4, 16), fill="x")

        # ------------------- CONTEÚDO PRINCIPAL (DIREITA) -------------------
        main_content = ctk.CTkFrame(self, fg_color=("#1b1b28", "#12121c"), corner_radius=0)
        main_content.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        main_content.grid_columnconfigure(0, weight=1)
        main_content.grid_rowconfigure(3, weight=1)

        # Top Bar: Status do Jogo Selecionado
        top_bar = ctk.CTkFrame(main_content, fg_color=("#222234", "#1a1a27"), corner_radius=12)
        top_bar.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 8))

        self.game_header_title = ctk.CTkLabel(
            top_bar,
            text=self.selected_game["game_name"] if self.selected_game else "Selecione um Jogo",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#ffffff"
        )
        self.game_header_title.pack(side="left", padx=16, pady=10)

        self.status_badge = ctk.CTkLabel(
            top_bar,
            text="● Desconectado",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#ff5555"
        )
        self.status_badge.pack(side="right", padx=16, pady=10)

        # Barra Speedhack Integrada
        speed_bar = ctk.CTkFrame(main_content, fg_color=("#242438", "#1b1b29"), corner_radius=10)
        speed_bar.grid(row=1, column=0, sticky="ew", padx=20, pady=4)

        speed_title = ctk.CTkLabel(speed_bar, text="⏱️ Speedhack Universal:", font=ctk.CTkFont(weight="bold"))
        speed_title.pack(side="left", padx=(14, 10), pady=8)

        self.speed_slider = ctk.CTkSlider(
            speed_bar,
            from_=0.25,
            to=5.0,
            number_of_steps=19,
            command=self._on_speed_changed
        )
        self.speed_slider.set(1.0)
        self.speed_slider.pack(side="left", fill="x", expand=True, padx=10, pady=8)

        self.speed_val_lbl = ctk.CTkLabel(speed_bar, text="1.0x (Normal)", width=90, font=ctk.CTkFont(weight="bold"))
        self.speed_val_lbl.pack(side="left", padx=5)

        reset_speed_btn = ctk.CTkButton(
            speed_bar,
            text="Reset (1x)",
            width=70,
            height=28,
            fg_color="#3a3a52",
            hover_color="#4d4d6e",
            command=self._reset_speed
        )
        reset_speed_btn.pack(side="right", padx=(5, 14), pady=8)

        # Ações Rápidas (Barra de Ferramentas)
        actions_bar = ctk.CTkFrame(main_content, fg_color="transparent")
        actions_bar.grid(row=2, column=0, sticky="ew", padx=20, pady=6)

        export_ct_btn = ctk.CTkButton(
            actions_bar,
            text="📄 Gerar Tabela .CT",
            fg_color="#0080ff",
            hover_color="#0066cc",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._export_cheat_table
        )
        export_ct_btn.pack(side="left", padx=(0, 10))

        mem_scan_btn = ctk.CTkButton(
            actions_bar,
            text="🔍 Memory Scanner Integrado",
            fg_color="#00a86b",
            hover_color="#008f5a",
            command=self._open_scanner_modal
        )
        mem_scan_btn.pack(side="left", padx=(0, 10))

        add_custom_btn = ctk.CTkButton(
            actions_bar,
            text="➕ Adicionar Cheat",
            fg_color="#2c2c40",
            hover_color="#3a3a55",
            command=self._open_add_cheat_modal
        )
        add_custom_btn.pack(side="left")

        # Lista de Cheats do Jogo
        self.cheats_container = ctk.CTkScrollableFrame(
            main_content,
            label_text="MODIFICADORES DE MEMÓRIA & CHEATS ATIVOS",
            fg_color=("#171724", "#101019")
        )
        self.cheats_container.grid(row=3, column=0, sticky="nsew", padx=20, pady=(4, 16))
        self._render_cheats_list()

    def _render_game_list(self):
        for widget in self.games_scroll.winfo_children():
            widget.destroy()

        for g in self.presets:
            is_active = self.selected_game and self.selected_game.get("id") == g.get("id")
            is_emu = EmulatorManager.is_emulator(g.get("process_name", ""))
            icon = "🕹️" if is_emu else "🎮"

            btn = ctk.CTkButton(
                self.games_scroll,
                text=f"{icon} {g['game_name']}",
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
        self.status_badge.configure(text=f"● Verificando ({self.mem.process_name})...", text_color="#ffcc00")
        self._setup_game_hotkeys()
        self._render_game_list()
        self._render_cheats_list()

        # Atualiza HUD para o jogo selecionado
        if self.hud and self.hud.root and self.selected_game:
            hud_dict = {c["description"]: self.active_cheats.get(c["id"], False) for c in self.selected_game.get("cheats", [])}
            self.hud.update_cheats(hud_dict)

    def _setup_game_hotkeys(self):
        """Desregistra atalhos anteriores e registra hotkeys globais para os cheats do jogo selecionado."""
        for hk in self._registered_hotkeys:
            try:
                keyboard.remove_hotkey(hk)
            except Exception:
                pass
        self._registered_hotkeys.clear()

        if not self.selected_game or not self.selected_game.get("cheats"):
            return

        for cheat in self.selected_game["cheats"]:
            hk_raw = cheat.get("hotkey", "")
            if hk_raw and hk_raw.lower() not in ["none", "nenhum", ""]:
                # Normaliza 'numpad 1' para 'num 1' aceito pelo módulo keyboard do Python
                norm_key = hk_raw.strip().lower().replace("numpad ", "num ").replace("numpad", "num ")
                try:
                    hk = keyboard.add_hotkey(
                        norm_key,
                        lambda c=cheat: self.after(0, lambda: self._toggle_live_cheat(c["id"], c, force_val=not self.active_cheats.get(c["id"], False))),
                        suppress=False
                    )
                    self._registered_hotkeys.append(hk)
                except Exception:
                    pass

    def _render_cheats_list(self):
        for widget in self.cheats_container.winfo_children():
            widget.destroy()

        self.cheat_switches.clear()

        if not self.selected_game or not self.selected_game.get("cheats"):
            empty_lbl = ctk.CTkLabel(
                self.cheats_container,
                text="Nenhum cheat configurado para este jogo ainda.",
                text_color="#6e6e8a"
            )
            empty_lbl.pack(pady=40)
            return

        for cheat in self.selected_game["cheats"]:
            cid = cheat["id"]
            card = ctk.CTkFrame(self.cheats_container, corner_radius=10, fg_color=("#222234", "#181826"))
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

            is_active = self.active_cheats.get(cid, False)
            switch = ctk.CTkSwitch(
                card,
                text="",
                progress_color="#00d2ff",
                command=lambda c_id=cid, c=cheat: self._toggle_live_cheat(c_id, c)
            )
            if is_active:
                switch.select()
            else:
                switch.deselect()
            switch.pack(side="right", padx=16)
            self.cheat_switches[cid] = switch

    def _toggle_live_cheat(self, cheat_id, cheat, force_val=None):
        if force_val is not None:
            new_val = force_val
        else:
            curr = self.active_cheats.get(cheat_id, False)
            new_val = not curr

        self.active_cheats[cheat_id] = new_val
        if new_val:
            # Associa com processo do jogo selecionado para isolamento de memória
            cheat["_process_name"] = self.selected_game.get("process_name", "") if self.selected_game else ""
            self.active_cheat_objects[cheat_id] = cheat
        else:
            self.active_cheat_objects.pop(cheat_id, None)

        # Sincroniza visual do switch se necessário
        sw = self.cheat_switches.get(cheat_id)
        if sw:
            try:
                if new_val and sw.get() != 1:
                    sw.select()
                elif not new_val and sw.get() != 0:
                    sw.deselect()
            except Exception:
                pass

        # Feedback sonoro assíncrono
        if new_val:
            SoundFeedback.play_cheat_on()
        else:
            SoundFeedback.play_cheat_off()

        # Atualiza HUD em tempo real exibindo lista completa com estados ATIVO / OFF
        if self.hud and self.hud.root and self.selected_game:
            hud_dict = {c["description"]: self.active_cheats.get(c["id"], False) for c in self.selected_game.get("cheats", [])}
            self.hud.update_cheats(hud_dict)

    def _start_cheat_enforcement_thread(self):
        """Thread daemon em segundo plano que executa freeze/write contínuo de valores na memória."""
        def _enforce_loop():
            while True:
                try:
                    if self.mem.is_connected and self.mem.pm:
                        active_items = list(self.active_cheat_objects.items())
                        connected_proc = getattr(self.mem, "_connected_process_name", "").lower()

                        for cid, cheat in active_items:
                            if not self.active_cheats.get(cid, False):
                                continue

                            # Isolamento de processo: não congelar valores de outro jogo
                            cheat_proc = cheat.get("_process_name", "").lower()
                            if cheat_proc and connected_proc and cheat_proc != connected_proc:
                                continue

                            addr_spec = cheat.get("address", cheat.get("base_offset"))
                            if addr_spec is None:
                                continue
                            offsets = cheat.get("offsets", [])
                            resolved_addr = self.mem.resolve_pointer(addr_spec, offsets)
                            if not resolved_addr or resolved_addr <= 0:
                                continue

                            cheat_type = str(cheat.get("type", "4 Bytes")).lower()
                            raw_val = cheat.get("default_value", cheat.get("value"))

                            if "float" in cheat_type:
                                val = float(raw_val) if raw_val is not None else 100.0
                                self.mem.write_float(resolved_addr, val)
                            elif "double" in cheat_type:
                                val = float(raw_val) if raw_val is not None else 100.0
                                self.mem.write_double(resolved_addr, val)
                            elif any(t in cheat_type for t in ["byte", "int", "binary"]):
                                val = int(raw_val) if raw_val is not None else 999
                                self.mem.write_int(resolved_addr, val)
                except Exception:
                    pass
                time.sleep(0.05) # 20 Hz (adequado para freeze sem sobrecarga de CPU)

        threading.Thread(target=_enforce_loop, daemon=True).start()

    def _import_external_ct(self):
        """Permite selecionar qualquer arquivo .CT baixado da internet e importar os cheats para o catálogo."""
        file_path = filedialog.askopenfilename(
            title="Selecionar Tabela do Cheat Engine (.CT)",
            filetypes=[("Cheat Engine Table", "*.ct"), ("Todos os Arquivos", "*.*")]
        )
        if not file_path:
            return

        parsed_game = CheatTableImporter.parse_ct_file(file_path)
        if not parsed_game or not parsed_game.get("cheats"):
            messagebox.showwarning("Importador .CT", "Nenhum cheat válido foi encontrado dentro desta tabela .CT.")
            return

        # Verifica se já existe um jogo com esse ID ou adiciona
        existing = next((p for p in self.presets if p["id"] == parsed_game["id"]), None)
        if existing:
            existing["cheats"].extend(parsed_game["cheats"])
            target_game = existing
        else:
            self.presets.append(parsed_game)
            target_game = parsed_game

        self._save_presets()
        self._select_game(target_game)
        messagebox.showinfo(
            "Tabela .CT Importada!",
            f"O jogo '{target_game['game_name']}' foi importado com {len(parsed_game['cheats'])} cheats com sucesso!"
        )

    def _on_speed_changed(self, val):
        val_rounded = round(val, 2)
        self.speed_val_lbl.configure(text=f"{val_rounded:.2f}x")
        self.speedhack.set_speed(val_rounded)

    def _reset_speed(self):
        self.speed_slider.set(1.0)
        self.speed_val_lbl.configure(text="1.0x (Normal)")
        self.speedhack.reset_speed()

    def _launch_hud(self):
        if not self.hud.root:
            self.hud.create_window()
            hud_dict = {c["description"]: True for c in self.active_cheat_objects.values()}
            self.hud.update_cheats(hud_dict)
        self.hud.toggle_visibility()

    def _sync_cloud(self):
        presets_path = os.path.join(os.path.dirname(__file__), "templates", "presets.json")
        added = CloudHub.sync_local_with_cloud(presets_path)
        self.presets = self._load_presets()
        self._render_game_list()
        messagebox.showinfo("Cloud Hub", f"Sincronização concluída!\nNovos presets adicionados: {added}")

    def _open_ai_assistant_modal(self):
        modal = ctk.CTkToplevel(self)
        modal.title("🤖 AI Cheat Assistant - Análise Estratégica")
        modal.geometry("560x480")
        modal.resizable(False, False)

        game_name = self.selected_game.get("game_name", "Jogo") if self.selected_game else "Jogo"
        engine_type = self.selected_game.get("engine_type", "Nativo / Custom") if self.selected_game else "Nativo"
        proc = self.selected_game.get("process_name", "") if self.selected_game else ""

        report = AIAssistantEngine.analyze_game(game_name, engine_type, proc)

        title_lbl = ctk.CTkLabel(modal, text=f"Análise de Engine: {game_name}", font=ctk.CTkFont(size=16, weight="bold"), text_color="#00d2ff")
        title_lbl.pack(pady=(16, 8), padx=20, anchor="w")

        box = ctk.CTkTextbox(modal, height=360)
        box.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        content = (
            f"🎮 Jogo: {report['game_name']}\n"
            f"⚙️ Engine Identificada: {report['engine_type']}\n"
            f"📍 Módulo Base Recomendado: {report['base_module']}\n\n"
            f"--- DIAGNÓSTICO E ESTRATÉGIA ---\n"
            f"{report['analysis']}\n\n"
            f"--- PADRÕES DE MEMÓRIA SUGERIDOS ---\n"
            f"{report['patterns']}\n\n"
        )
        for p in report["patterns"]:
            content += f"• {p['name']}: {p['hint']}\n"

        content += f"\n--- TIPOS DE DADOS MAIS EFICAZES ---\n"
        for t in report["recommended_types"]:
            content += f"✓ {t}\n"

        box.insert("end", content)
        box.configure(state="disabled")

    def _open_scanner_modal(self):
        modal = ctk.CTkToplevel(self)
        modal.title("🔍 CheatCraft Memory Scanner")
        modal.geometry("520x460")
        modal.resizable(False, False)

        header_lbl = ctk.CTkLabel(modal, text="Scanner de Memória em Tempo Real", font=ctk.CTkFont(size=15, weight="bold"))
        header_lbl.pack(pady=(15, 5))

        input_frame = ctk.CTkFrame(modal, fg_color="transparent")
        input_frame.pack(fill="x", padx=20, pady=5)

        val_entry = ctk.CTkEntry(input_frame, placeholder_text="Valor atual no jogo (ex: 100)")
        val_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        type_combo = ctk.CTkComboBox(input_frame, values=["4 Bytes", "Float"], width=120)
        type_combo.pack(side="right")

        btn_frame = ctk.CTkFrame(modal, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)

        results_box = ctk.CTkTextbox(modal, height=220)
        results_box.pack(fill="both", expand=True, padx=20, pady=5)

        def do_first_scan():
            v = val_entry.get().strip()
            if not v:
                return
            fs_btn.configure(state="disabled")
            ns_btn.configure(state="disabled")
            results_box.delete("1.0", "end")
            results_box.insert("end", f"Buscando '{v}' na memória do processo em segundo plano...\nPor favor, aguarde...\n")
            val_type = type_combo.get()

            def _scan_worker():
                try:
                    if not self.mem.pm:
                        def _show_err():
                            try:
                                if modal.winfo_exists():
                                    results_box.delete("1.0", "end")
                                    results_box.insert("end", "Erro: Processo do jogo não está conectado!\n")
                            except Exception:
                                pass
                        try:
                            if modal.winfo_exists():
                                modal.after(0, _show_err)
                        except Exception:
                            pass
                        return

                    self.scanner.set_process(self.mem.pm)
                    res = self.scanner.first_scan(v, val_type=val_type)

                    def _show_res():
                        try:
                            if modal.winfo_exists():
                                results_box.delete("1.0", "end")
                                results_box.insert("end", f"Concluído! Encontrados {len(res)} endereços.\n\n")
                                for a in res[:30]:
                                    results_box.insert("end", f"0x{a:08X}\n")
                                if len(res) > 30:
                                    results_box.insert("end", f"... e mais {len(res)-30} endereços.\n")
                        except Exception:
                            pass

                    try:
                        if modal.winfo_exists():
                            modal.after(0, _show_res)
                    except Exception:
                        pass
                except Exception as ex:
                    def _show_exc():
                        try:
                            if modal.winfo_exists():
                                results_box.delete("1.0", "end")
                                results_box.insert("end", f"Erro durante First Scan: {ex}\n")
                        except Exception:
                            pass
                    try:
                        if modal.winfo_exists():
                            modal.after(0, _show_exc)
                    except Exception:
                        pass
                finally:
                    def _reenable():
                        try:
                            if modal.winfo_exists():
                                fs_btn.configure(state="normal")
                                ns_btn.configure(state="normal")
                        except Exception:
                            pass
                    try:
                        if modal.winfo_exists():
                            modal.after(0, _reenable)
                    except Exception:
                        pass

            threading.Thread(target=_scan_worker, daemon=True).start()

        def do_next_scan():
            v = val_entry.get().strip()
            if not v:
                return
            fs_btn.configure(state="disabled")
            ns_btn.configure(state="disabled")
            results_box.delete("1.0", "end")
            results_box.insert("end", f"Filtrando para novo valor '{v}' em segundo plano...\nPor favor, aguarde...\n")
            val_type = type_combo.get()

            def _next_worker():
                try:
                    if not self.mem.pm:
                        def _show_err():
                            try:
                                if modal.winfo_exists():
                                    results_box.delete("1.0", "end")
                                    results_box.insert("end", "Erro: Processo do jogo não está conectado!\n")
                            except Exception:
                                pass
                        try:
                            if modal.winfo_exists():
                                modal.after(0, _show_err)
                        except Exception:
                            pass
                        return

                    res = self.scanner.next_scan(v, val_type=val_type)

                    def _show_res():
                        try:
                            if modal.winfo_exists():
                                results_box.delete("1.0", "end")
                                results_box.insert("end", f"Concluído! Restaram {len(res)} endereços filtrados:\n\n")
                                for a in res[:30]:
                                    results_box.insert("end", f"0x{a:08X}\n")
                                if len(res) > 30:
                                    results_box.insert("end", f"... e mais {len(res)-30} endereços.\n")
                        except Exception:
                            pass

                    try:
                        if modal.winfo_exists():
                            modal.after(0, _show_res)
                    except Exception:
                        pass
                except Exception as ex:
                    def _show_exc():
                        try:
                            if modal.winfo_exists():
                                results_box.delete("1.0", "end")
                                results_box.insert("end", f"Erro durante Next Scan: {ex}\n")
                        except Exception:
                            pass
                    try:
                        if modal.winfo_exists():
                            modal.after(0, _show_exc)
                    except Exception:
                        pass
                finally:
                    def _reenable():
                        try:
                            if modal.winfo_exists():
                                fs_btn.configure(state="normal")
                                ns_btn.configure(state="normal")
                        except Exception:
                            pass
                    try:
                        if modal.winfo_exists():
                            modal.after(0, _reenable)
                    except Exception:
                        pass

            threading.Thread(target=_next_worker, daemon=True).start()

        fs_btn = ctk.CTkButton(btn_frame, text="First Scan", fg_color="#0080ff", hover_color="#0066cc", command=do_first_scan)
        fs_btn.pack(side="left", padx=(0, 10), fill="x", expand=True)

        ns_btn = ctk.CTkButton(btn_frame, text="Next Scan", fg_color="#00a86b", hover_color="#008f5a", command=do_next_scan)
        ns_btn.pack(side="right", fill="x", expand=True)

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
            self._save_presets()
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
                if not any(p["process_name"].lower() == d["executable"].lower() for p in self.presets):
                    self.presets.append({
                        "id": d["name"].lower().replace(" ", "_"),
                        "game_name": f"{d['name']} ({d['engine_type']})",
                        "engine_type": d["engine_type"],
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
                        if not self.was_connected:
                            SoundFeedback.play_connected()
                            self.was_connected = True
                        self.after(0, lambda: self.status_badge.configure(
                            text=f"● Conectado ({proc_name})", text_color="#00ff66"
                        ))
                    else:
                        if self.was_connected:
                            SoundFeedback.play_disconnected()
                            self.was_connected = False
                        self.after(0, lambda: self.status_badge.configure(
                            text=f"● Desconectado ({proc_name})", text_color="#ff5555"
                        ))
                time.sleep(1.5)

        threading.Thread(target=monitor, daemon=True).start()

    def destroy(self):
        """Limpa hotkeys globais, encerra HUD/mira e desconecta com segurança."""
        for hk in self._registered_hotkeys:
            try:
                keyboard.remove_hotkey(hk)
            except Exception:
                pass
        self._registered_hotkeys.clear()

        if hasattr(self, "_insert_hotkey") and self._insert_hotkey:
            try:
                keyboard.remove_hotkey(self._insert_hotkey)
            except Exception:
                pass
            self._insert_hotkey = None

        if hasattr(self, "hud") and self.hud:
            try:
                self.hud.destroy()
            except Exception:
                pass

        if hasattr(self, "mem") and self.mem:
            try:
                self.mem.disconnect()
            except Exception:
                pass

        super().destroy()

if __name__ == "__main__":
    app = CheatCraftApp()
    app.mainloop()
