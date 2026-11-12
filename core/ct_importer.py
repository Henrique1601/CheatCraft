import os
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional

class CheatTableImporter:
    """
    Parser universal de arquivos .CT (Cheat Engine Tables) da internet.
    Lê a estrutura XML do arquivo .CT, extrai CheatEntries, endereços base,
    offsets de ponteiros, variáveis e scripts Auto-Assembler, convertendo
    tudo para o formato nativo do CheatCraft.
    """

    @staticmethod
    def parse_ct_file(file_path: str, game_name_hint: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if not os.path.exists(file_path):
            return None

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            # Tenta inferir nome do processo pelo Script Lua se houver
            lua_el = root.find("LuaScript")
            process_name = "game.exe"
            if lua_el is not None and lua_el.text:
                lua_txt = lua_el.text
                if "openProcess(" in lua_txt:
                    try:
                        part = lua_txt.split("openProcess(")[1].split(")")[0]
                        process_name = part.replace('"', '').replace("'", '').strip()
                    except Exception:
                        pass

            # Nome do jogo a partir do arquivo
            base_filename = os.path.basename(file_path)
            clean_name = game_name_hint or base_filename.replace(".ct", "").replace("_", " ").title()

            cheats: List[Dict[str, Any]] = []
            cheat_entries_el = root.find("CheatEntries")

            if cheat_entries_el is not None:
                for idx, entry in enumerate(cheat_entries_el.findall("CheatEntry")):
                    desc_el = entry.find("Description")
                    desc = desc_el.text.strip('"') if desc_el is not None and desc_el.text else f"Cheat #{idx+1}"

                    var_type_el = entry.find("VariableType")
                    var_type = var_type_el.text if var_type_el is not None and var_type_el.text else "4 Bytes"

                    addr_el = entry.find("Address")
                    addr = addr_el.text if addr_el is not None and addr_el.text else f'"{process_name}"+0'

                    # Extrai offsets se existirem
                    offsets: List[int] = []
                    offsets_el = entry.find("Offsets")
                    if offsets_el is not None:
                        for off in offsets_el.findall("Offset"):
                            if off.text:
                                off_text = off.text.strip()
                                try:
                                    offsets.append(int(off_text, 16))
                                except ValueError:
                                    try:
                                        offsets.append(int(off_text))
                                    except ValueError:
                                        pass

                    # Extrai hotkey se houver
                    hotkey = f"NUMPAD {min(idx + 1, 9)}"
                    hotkeys_el = entry.find("Hotkeys")
                    if hotkeys_el is not None:
                        hk_key = hotkeys_el.find(".//Key")
                        if hk_key is not None and hk_key.text:
                            hotkey = hk_key.text

                    cheats.append({
                        "id": f"imported_{idx+1}",
                        "description": desc,
                        "type": var_type,
                        "address": addr,
                        "offsets": offsets,
                        "hotkey": hotkey
                    })

            return {
                "id": clean_name.lower().replace(" ", "_").replace("'", ""),
                "game_name": clean_name,
                "engine_type": "Nativo / Importado",
                "process_name": process_name,
                "cheats": cheats
            }

        except Exception as e:
            print(f"Erro ao parsear arquivo .CT: {e}")
            return None
