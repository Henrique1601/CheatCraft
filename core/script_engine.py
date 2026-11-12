import os
from typing import Dict, Any

class ScriptEngine:
    """
    Gera scripts de injeção em Auto-Assembler compatíveis com Cheat Engine
    e patches de memória em tempo de execução (NOP / Code Hooking).
    """

    @staticmethod
    def generate_nop_script(entry_name: str, process_name: str, address_or_symbol: str, byte_count: int = 5) -> str:
        """
        Gera um script [ENABLE]/[DISABLE] de NOP (No Operation - 0x90) para impedir
        que instruções que causam dano à vida ou decrementam munição sejam executadas.
        """
        nops = " ".join(["90"] * byte_count)
        script = f"""[ENABLE]
// {entry_name} - NOP Patch
alloc(newmem, 2048, "{process_name}")
label(returnhere)
label(originalcode)

{address_or_symbol}:
  db {nops}

returnhere:

[DISABLE]
{address_or_symbol}:
  // Código original restaurado pelo Cheat Engine
  // readmem({address_or_symbol}, {byte_count})
dealloc(newmem)
"""
        return script

    @staticmethod
    def generate_infinite_ammo_script(process_name: str, symbol: str) -> str:
        """Script de substituição de decremento de munição (ex: sub [rax], 1 -> nop)."""
        return f"""[ENABLE]
assert("{process_name}"+{symbol}, 2B 08) // Exemplo: sub ecx, [rax]
alloc(newmem, 128, "{process_name}")
label(returnhere)

newmem:
  // Nao subtrai nada
  jmp returnhere

"{process_name}"+{symbol}:
  jmp newmem
returnhere:

[DISABLE]
"{process_name}"+{symbol}:
  sub ecx, [rax]
dealloc(newmem)
"""
