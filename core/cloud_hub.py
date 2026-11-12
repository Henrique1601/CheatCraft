import os
import json
import urllib.request
from typing import List, Dict, Any

class CloudHub:
    """
    Sincroniza tabelas, cheats e presets da comunidade a partir de fontes na nuvem
    e repositórios oficiais/comunitários do GitHub.
    """
    COMMUNITY_URL = "https://raw.githubusercontent.com/Henrique1601/CheatCraft/main/templates/community_presets.json"

    @classmethod
    def fetch_community_presets(cls) -> List[Dict[str, Any]]:
        """Busca catálogo de presets atualizados na nuvem."""
        try:
            req = urllib.request.Request(
                cls.COMMUNITY_URL,
                headers={"User-Agent": "CheatCraft-Studio/2.0"}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    return data.get("presets", [])
        except Exception:
            pass
        return []

    @classmethod
    def sync_local_with_cloud(cls, local_presets_path: str) -> int:
        """
        Mescla novos presets da nuvem no arquivo local sem sobrescrever cheats customizados.
        Retorna o total de novos presets adicionados.
        """
        cloud_presets = cls.fetch_community_presets()
        if not cloud_presets or not os.path.exists(local_presets_path):
            return 0

        added_count = 0
        try:
            with open(local_presets_path, "r", encoding="utf-8") as f:
                local_data = json.load(f)

            local_presets = local_data.get("presets", [])
            local_ids = {p.get("id") for p in local_presets}

            for cp in cloud_presets:
                if cp.get("id") not in local_ids:
                    local_presets.append(cp)
                    added_count += 1

            if added_count > 0:
                local_data["presets"] = local_presets
                with open(local_presets_path, "w", encoding="utf-8") as f:
                    json.dump(local_data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"Erro ao sincronizar presets: {e}")

        return added_count
