import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import List, Dict, Any, Optional

class CheatTableGenerator:
    """
    Gera tabelas nativas .CT do Cheat Engine em formato XML perfeitamente estruturado,
    suportando CheatEntries com endereços diretos, cadeias multinível de ponteiros
    e scripts de Auto Assembler ([ENABLE] / [DISABLE]).
    """
    
    @staticmethod
    def generate_ct(
        game_title: str,
        process_name: str,
        entries: List[Dict[str, Any]],
        output_path: str,
        lua_script: Optional[str] = None
    ) -> str:
        """
        Cria um arquivo .CT com as entradas especificadas.
        
        entry format:
        {
            "id": 0,
            "description": "God Mode",
            "type": "Float" | "4 Bytes" | "Binary" | "Auto Assembler Script",
            "address": '"spiderman.exe"+01A2B3C0' ou '0x12345678',
            "offsets": [0x48, 0x10, 0x0], # opcional
            "script": "[ENABLE]...", # se for Auto Assembler
            "hotkey": "NUMPAD 1" # opcional
        }
        """
        root = ET.Element("CheatTable", CheatEngineTableVersion="45")
        
        # Bloco de Entradas (CheatEntries)
        cheat_entries_el = ET.SubElement(root, "CheatEntries")
        
        for idx, entry in enumerate(entries):
            entry_id = entry.get("id", idx)
            entry_el = ET.SubElement(cheat_entries_el, "CheatEntry")
            
            ET.SubElement(entry_el, "ID").text = str(entry_id)
            ET.SubElement(entry_el, "Description").text = f'"{entry.get("description", "Novo Cheat")}"'
            
            var_type = entry.get("type", "4 Bytes")
            
            # Tratamento de Script vs Endereço/Ponteiro
            if var_type == "Auto Assembler Script" or "script" in entry:
                ET.SubElement(entry_el, "VariableType").text = "Auto Assembler Script"
                script_el = ET.SubElement(entry_el, "AssemblerScript")
                script_el.text = entry.get("script", "")
            else:
                ET.SubElement(entry_el, "VariableType").text = var_type
                addr = entry.get("address", f'"{process_name}"+0')
                ET.SubElement(entry_el, "Address").text = str(addr)
                
                # O Cheat Engine espera offsets na ordem bottom-up (de baixo para cima) no XML
                offsets = entry.get("offsets", [])
                if offsets:
                    offsets_el = ET.SubElement(entry_el, "Offsets")
                    for off in reversed(offsets):
                        off_str = hex(off) if isinstance(off, int) else str(off)
                        ET.SubElement(offsets_el, "Offset").text = off_str.replace("0x", "").upper()
            
            # Hotkeys opcionais no Cheat Engine
            if "hotkey" in entry:
                hotkeys_el = ET.SubElement(entry_el, "Hotkeys")
                hk_el = ET.SubElement(hotkeys_el, "Hotkey")
                action_el = ET.SubElement(hk_el, "Action")
                action_el.text = "Toggle Activation"
                keys_el = ET.SubElement(hk_el, "Keys")
                ET.SubElement(keys_el, "Key").text = entry["hotkey"]
                ET.SubElement(hk_el, "ID").text = "0"
        
        # Script LUA opcional de auto-attach
        lua_el = ET.SubElement(root, "LuaScript")
        if lua_script:
            lua_el.text = lua_script
        else:
            default_lua = (
                f"-- CheatCraft Auto-Attach Script\n"
                f'local process = "{process_name}"\n'
                f"local function checkGame()\n"
                f"  if getOpenedProcessID() == 0 then\n"
                f"    openProcess(process)\n"
                f"  end\n"
                f"end\n"
                f"local t = createTimer(nil)\n"
                f"timer_setInterval(t, 2000)\n"
                f"timer_onTimer(t, checkGame)\n"
            )
            lua_el.text = default_lua
            
        # Formata com indentação bonita
        xml_str = ET.tostring(root, encoding="utf-8")
        parsed = minidom.parseString(xml_str)
        pretty_xml = parsed.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")
        
        # Garante diretório pai
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(pretty_xml)
            
        return output_path
