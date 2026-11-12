import os
import winreg
from typing import List, Dict, Any

class GameScanner:
    """
    Detecta instalações do Steam e bibliotecas de jogos no Windows,
    além de listar processos em execução com executáveis correspondentes.
    """
    
    @staticmethod
    def get_steam_path() -> str:
        """Obtém o caminho do Steam a partir do Registro do Windows."""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam")
            path, _ = winreg.QueryValueEx(key, "SteamPath")
            winreg.CloseKey(key)
            return path.replace("/", "\\")
        except Exception:
            # Fallback para caminho comum em 64-bit
            default_path = r"C:\Program Files (x86)\Steam"
            return default_path if os.path.exists(default_path) else ""

    @classmethod
    def get_steam_library_folders(cls) -> List[str]:
        """Lê os caminhos das pastas de biblioteca adicionais do Steam (libraryfolders.vdf)."""
        steam_path = cls.get_steam_path()
        if not steam_path:
            return []

        folders = [os.path.join(steam_path, "steamapps", "common")]
        vdf_path = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
        
        if os.path.exists(vdf_path):
            try:
                with open(vdf_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        line_clean = line.strip()
                        if '"path"' in line_clean:
                            parts = line_clean.split('"path"')
                            if len(parts) > 1:
                                p = parts[1].replace('"', '').strip().replace('\\\\', '\\')
                                common_p = os.path.join(p, "steamapps", "common")
                                if os.path.exists(common_p) and common_p not in folders:
                                    folders.append(common_p)
            except Exception:
                pass

        return [f for f in folders if os.path.exists(f)]

    @classmethod
    def scan_installed_games(cls) -> List[Dict[str, Any]]:
        """Varre os diretórios do Steam e retorna lista de jogos e executáveis encontrados."""
        libraries = cls.get_steam_library_folders()
        games = []

        for lib in libraries:
            try:
                for entry in os.scandir(lib):
                    if entry.is_dir():
                        game_name = entry.name
                        exes = []
                        # Procura executáveis na raiz do jogo
                        for file in os.scandir(entry.path):
                            if file.is_file() and file.name.lower().endswith(".exe"):
                                # Ignora desinstaladores e crash reporters comuns
                                if not any(ign in file.name.lower() for ign in ["crash", "unins", "report", "redist", "setup"]):
                                    exes.append(file.name)
                                    
                        if exes:
                            games.append({
                                "name": game_name,
                                "path": entry.path,
                                "executable": exes[0],
                                "available_exes": exes,
                                "engine_type": cls._detect_engine(entry.path)
                            })
            except Exception:
                continue

        return games

    @staticmethod
    def _detect_engine(game_path: str) -> str:
        """Tenta inferir a engine (Unity, Unreal, Custom) pela estrutura de pastas."""
        try:
            for item in os.listdir(game_path):
                if item.endswith("_Data") or "MonoBleedingEdge" in item or "UnityCrashHandler" in item:
                    return "Unity"
                if item in ["Engine", "Binaries"] or item.endswith(".uproject"):
                    return "Unreal Engine"
        except Exception:
            pass
        return "Nativo / Custom"
