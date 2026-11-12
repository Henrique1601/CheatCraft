from typing import Dict, Any, List

class AIAssistantEngine:
    """
    Motor inteligente de análise de executáveis e engines de jogos.
    Recomenda offsets prováveis, estruturas de dados típicas e padrões AOB
    de acordo com a engine detectada (Unity, Unreal Engine, Godot ou Nativo C++).
    """

    ENGINE_KNOWLEDGE_BASE = {
        "Unity": {
            "description": "Jogos desenvolvidos em Unity utilizam Mono ou IL2CPP. As variáveis de player costumam ficar em UnityPlayer.dll.",
            "recommended_base_module": "UnityPlayer.dll",
            "common_patterns": [
                {"name": "Health Component Offset", "hint": "Geralmente alocado em classes como PlayerHealth, offset típico entre 0x20 e 0x58."},
                {"name": "TimeScale Offset", "hint": "UnityPlayer.dll Time.timeScale (Float entre 0.0 e 100.0)."}
            ],
            "recommended_types": ["Float (Health)", "4 Bytes (Coins/XP)", "Double (High Precision Money)"]
        },
        "Unreal Engine": {
            "description": "Jogos em Unreal Engine 4/5 usam UWorld -> PersistentLevel -> OwningGameInstance -> LocalPlayers.",
            "recommended_base_module": "<process_name>",
            "common_patterns": [
                {"name": "GWorld / UWorld Pointer", "hint": "Ponteiro principal de acesso às entidades e atores do mapa."},
                {"name": "APawn / ACharacter", "hint": "Contém a instância do jogador e HealthComponent nativo."}
            ],
            "recommended_types": ["Float (Vida, Stamina)", "4 Bytes (Munição)", "Float (Velocidade)"]
        },
        "Nativo / Custom": {
            "description": "Jogo compilado diretamente em C/C++ x86/x64. Utiliza estruturas estáticas ou alocações em heap.",
            "recommended_base_module": "<process_name>",
            "common_patterns": [
                {"name": "Array of Bytes (AOB)", "hint": "Ideal buscar instruções como 'sub [rax+offset], ecx' para isolar a função que aplica dano."},
                {"name": "Pointer Chain Scan", "hint": "Cadeias multinível de 3 a 5 offsets a partir do base module .exe."}
            ],
            "recommended_types": ["4 Bytes", "Float", "Auto Assembler Script (NOP Injection)"]
        }
    }

    @classmethod
    def analyze_game(cls, game_name: str, engine_type: str, process_name: str) -> Dict[str, Any]:
        """Gera recomendações sob medida para o jogo selecionado."""
        profile = cls.ENGINE_KNOWLEDGE_BASE.get(engine_type, cls.ENGINE_KNOWLEDGE_BASE["Nativo / Custom"])
        
        return {
            "game_name": game_name,
            "engine_type": engine_type,
            "process_name": process_name,
            "analysis": profile["description"],
            "base_module": profile["recommended_base_module"].replace("<process_name>", process_name),
            "patterns": profile["common_patterns"],
            "recommended_types": profile["recommended_types"]
        }
