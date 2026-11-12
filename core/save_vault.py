import os
import shutil
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

class SaveGameVault:
    """
    Localizador e gerenciador de backups de arquivos de SaveGame para jogos de PC.
    Detecta locais comuns (Saved Games, AppData Local/Roaming, Documentos) e cria
    snapshots com timestamp para restauração segura com 1 clique.
    """

    DEFAULT_BACKUP_ROOT = os.path.join(os.environ.get("USERPROFILE", "C:\\"), "CheatCraft_SaveBackups")

    # Mapeamento de pastas comuns de saves por ID de jogo
    KNOWN_SAVE_PATHS = {
        "eldenring": [
            os.path.join(os.environ.get("APPDATA", ""), "EldenRing"),
        ],
        "cyberpunk_2077": [
            os.path.join(os.environ.get("USERPROFILE", ""), "Saved Games", "CD Projekt Red", "Cyberpunk 2077")
        ],
        "witcher3": [
            os.path.join(os.environ.get("USERPROFILE", ""), "Documents", "The Witcher 3", "gamesaves")
        ],
        "sekiro": [
            os.path.join(os.environ.get("APPDATA", ""), "Sekiro")
        ],
        "dark_souls_3": [
            os.path.join(os.environ.get("APPDATA", ""), "DarkSoulsIII")
        ],
        "hollow_knight": [
            os.path.join(os.environ.get("USERPROFILE", ""), "AppData", "LocalLow", "Team Cherry", "Hollow Knight")
        ],
        "spiderman": [
            os.path.join(os.environ.get("USERPROFILE", ""), "Documents", "Marvel's Spider-Man Remastered")
        ],
        "gta5": [
            os.path.join(os.environ.get("USERPROFILE", ""), "Documents", "Rockstar Games", "GTA V", "Profiles")
        ],
        "rdr2": [
            os.path.join(os.environ.get("USERPROFILE", ""), "Documents", "Rockstar Games", "Red Dead Redemption 2", "Profiles")
        ]
    }

    @classmethod
    def find_save_folder(cls, game_id: str) -> Optional[str]:
        """Tenta encontrar a pasta de savegame real do jogo ativo no PC do usuário."""
        candidates = cls.KNOWN_SAVE_PATHS.get(game_id, [])
        for p in candidates:
            if os.path.exists(p):
                return p

        # Busca genérica em "Saved Games"
        generic_saved_games = os.path.join(os.environ.get("USERPROFILE", ""), "Saved Games")
        if os.path.exists(generic_saved_games):
            for d in os.listdir(generic_saved_games):
                if game_id.replace("_", "") in d.lower().replace(" ", ""):
                    full_p = os.path.join(generic_saved_games, d)
                    if os.path.isdir(full_p):
                        return full_p

        return None

    @classmethod
    def create_backup(cls, game_id: str, custom_save_dir: Optional[str] = None) -> Dict[str, Any]:
        """Cria um snapshot compactado/copiado da pasta de save atual."""
        save_dir = custom_save_dir or cls.find_save_folder(game_id)
        if not save_dir or not os.path.exists(save_dir):
            return {"success": False, "message": "Pasta de SaveGame não encontrada no computador."}

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            game_backup_dir = os.path.join(cls.DEFAULT_BACKUP_ROOT, game_id)
            os.makedirs(game_backup_dir, exist_ok=True)

            backup_dest = os.path.join(game_backup_dir, f"backup_{timestamp}")
            shutil.copytree(save_dir, backup_dest)

            return {
                "success": True,
                "message": f"Backup criado com sucesso em:\n{backup_dest}",
                "path": backup_dest,
                "timestamp": timestamp
            }
        except Exception as e:
            return {"success": False, "message": f"Falha ao criar backup: {e}"}

    @classmethod
    def list_backups(cls, game_id: str) -> List[Dict[str, Any]]:
        """Lista backups existentes para o jogo especificado."""
        game_backup_dir = os.path.join(cls.DEFAULT_BACKUP_ROOT, game_id)
        if not os.path.exists(game_backup_dir):
            return []

        backups = []
        try:
            for item in os.listdir(game_backup_dir):
                full_p = os.path.join(game_backup_dir, item)
                if os.path.isdir(full_p) and item.startswith("backup_"):
                    backups.append({
                        "name": item,
                        "path": full_p,
                        "date": datetime.fromtimestamp(os.path.getmtime(full_p)).strftime("%d/%m/%Y %H:%M:%S")
                    })
        except Exception:
            pass

        return sorted(backups, key=lambda x: x["name"], reverse=True)

    @classmethod
    def restore_backup(cls, game_id: str, backup_path: str, custom_save_dir: Optional[str] = None) -> Dict[str, Any]:
        """Restaura um backup salvo previamente para a pasta do jogo."""
        save_dir = custom_save_dir or cls.find_save_folder(game_id)
        if not save_dir:
            return {"success": False, "message": "Diretório de destino do save não encontrado."}

        if not os.path.exists(backup_path):
            return {"success": False, "message": "Arquivo de backup não encontrado."}

        try:
            # Substitui o conteúdo da pasta de save
            if os.path.exists(save_dir):
                shutil.rmtree(save_dir)
            shutil.copytree(backup_path, save_dir)
            return {"success": True, "message": "SaveGame restaurado com sucesso!"}
        except Exception as e:
            return {"success": False, "message": f"Falha ao restaurar save: {e}"}
