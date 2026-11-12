# 🎮 CheatCraft Studio

> **Universal Single-Player Game Modder, Trainer Hub & Cheat Engine (.CT) Generator**

**CheatCraft** é um aplicativo desktop moderno para Windows focado em modding, criação de cheats e manipulação de memória para jogos singleplayer offline. Ele combina a facilidade de uso de um hub estilo WeMod com a flexibilidade técnica de exportação direta para tabelas nativas `.CT` do Cheat Engine (XML + Lua auto-attach).

---

## ✨ Funcionalidades Principais

* 🚀 **Launcher & UI Moderna (CustomTkinter)**: Interface escura moderna com temas gamer, cards dinâmicos e controle por switches.
* 📄 **Gerador de Tabelas `.CT` (Cheat Engine)**: Exportação com 1 clique de arquivos `.CT` nativos em XML, contendo `CheatEntries`, endereços base de módulos, cadeias multiníveis de ponteiros, tipos de variáveis e scripts de auto-assembly.
* 🔍 **Scanner de Bibliotecas Steam**: Detecção automática de jogos instalados no PC e inferência da engine utilizada (*Unity*, *Unreal Engine*, *Custom/Nativo*).
* ⚡ **Trainer Runtime em Tempo Real (Pymem)**: Hook direto de processos, resolução de ponteiros 64-bit e loop suave de congelamento de valores (20 Hz) sem sobrecarga de CPU.
* ⌨️ **Hotkeys Globais**: Ativação e desativação de cheats durante o jogo via teclado numérico (`Num 1` a `Num 6`), sem necessidade de Alt+Tab.
* 🎯 **Presets Inclusos**:
  - **Marvel's Spider-Man Remastered** (God Mode, Foco Infinito, Gadgets Ilimitados, Combo 999x, Speedhack).
  - **Template Genérico Unity (Mono)** (Vida, Dinheiro/Moedas, Stamina).
  - **Template Genérico Unreal Engine 4/5** (God Mode, Munição Infinita).

---

## 🛠️ Tecnologias

- **Python 3.10+**
- **CustomTkinter** (Interface gráfica responsiva com tema escuro)
- **Pymem** (Manipulação e leitura de memória de processos 64-bit no Windows)
- **Keyboard** (Captura de atalhos globais de teclado)
- **XML minidom / ElementTree** (Serialização de Cheat Tables .CT)

---

## 🚀 Como Executar

### 1. Instalar dependências
```powershell
pip install -r requirements.txt
```

### 2. Iniciar o CheatCraft
Execute com duplo clique no arquivo:
```cmd
iniciar_cheatcraft.bat
```
Ou via terminal:
```powershell
python launcher.py
```

---

## 🗺️ Roadmap de Novas Melhorias

- [ ] **Scanner AOB Integrado na UI**: Localização de endereços desconhecidos direto pelo app.
- [ ] **Overlay In-Game DirectX / ImGui**: HUD flutuante semi-transparente dentro do jogo.
- [ ] **Comunidade & Cloud Sync**: Baixar e compartilhar tabelas `.CT` e presets da comunidade.
- [ ] **Suporte a Emuladores**: Presets para RPCS3, PCSX2, Dolphin e Yuzu/Ryujinx.
- [ ] **Speedhack Global via DLL Hook**: Acelerar ou desacelerar o tempo do jogo diretamente na memória.

---

## ⚖️ Aviso Legal / Disclaimer

O **CheatCraft** foi desenvolvido exclusivamente para fins educacionais e uso em jogos **singleplayer offline**. Não utilize em jogos multiplayer ou com sistemas anti-cheat (Easy Anti-Cheat, BattlEye, VAC, etc.), respeitando os termos de serviço das desenvolvedoras.
