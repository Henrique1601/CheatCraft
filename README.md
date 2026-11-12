# 🎮 CheatCraft Studio v3.0 Pro

> **Universal Single-Player Game Modder, Trainer Hub & Cheat Engine (.CT) Studio**

[![GitHub Release](https://img.shields.io/badge/release-v3.0--pro-00d2ff.svg)](https://github.com/Henrique1601/CheatCraft)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%20%7C%2011-orange.svg)](#)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](#)

**CheatCraft Studio** é uma plataforma Desktop completa para Windows focada em modding, criação de cheats, engenharia reversa e manipulação de memória para jogos singleplayer offline. 

Ele combina a experiência moderna e visual de ferramentas como *WeMod* com o poder técnico de exportação para tabelas nativas `.CT` do **Cheat Engine** (XML estruturado + Lua auto-attach).

---

## ✨ Funcionalidades Principais (v3.0 Pro)

* 🚀 **Auto-Attach Silencioso & Feedback Sonoro (`core/sound_feedback.py`)**: Conexão instantânea em segundo plano com o processo do jogo assim que ele é aberto, acompanhado de beeps sonoros sutis no padrão Windows indicando conexão e ativação de cheats.
* ⏱️ **Speedhack Universal (`core/speedhack_controller.py`)**: Controle deslizante na interface para acelerar ou desacelerar o tempo do jogo de **0.25x** (câmera lenta para esquivas) até **5.0x / 10.0x** (pular cutscenes e grind).
* 🤖 **AI Cheat Assistant (`core/ai_assistant.py`)**: Análise inteligente da engine do jogo (*Unity*, *Unreal Engine*, *Godot*, *C++ Nativo*) com recomendações de módulos base, offsets típicos e assinaturas AOB.
* 🔍 **Memory Scanner Integrado (`core/memory_scanner.py`)**: First Scan e Next Scan direto no aplicativo para encontrar endereços dinâmicos na RAM sem depender de softwares de terceiros.
* 🪟 **In-Game HUD Overlay Transparente (`core/hud_overlay.py`)**: Painel flutuante sobreposto à tela do jogo com ativação pela tecla **`[Insert]`**.
* 🌐 **Cloud Hub de Tabelas (`core/cloud_hub.py`)**: Sincronização e download com 1 clique de presets da comunidade no GitHub.
* 🕹️ **Módulo de Emuladores de Console (`core/emulator_manager.py`)**: Mapeamento de memória virtual para **RPCS3** (PS3), **PCSX2** (PS2), **Dolphin** (GameCube/Wii) e **Cemu** (Wii U).
* 📄 **Gerador de Tabelas `.CT` (Cheat Engine)**: Exportação com 1 clique de arquivos `.CT` nativos em XML, contendo endereços, offsets multiníveis, tipos de variáveis e scripts de auto-assembly.
* 📦 **Script de Build Standalone (`build_exe.bat`)**: Compilação automatizada com PyInstaller em executável nativo `.exe`.

---

## 🚀 Como Executar

### 1. Iniciar via Python
```powershell
pip install -r requirements.txt
python launcher.py
```
Ou com duplo clique em [`iniciar_cheatcraft.bat`](file:///c:/Users/Public/Downloads/scripts%20para%20jogos/iniciar_cheatcraft.bat).

### 2. Compilar Executável Portátil (.exe)
Dê um duplo clique no script:
```cmd
build_exe.bat
```
O executável standalone será gerado em `dist/CheatCraft_Studio/CheatCraft_Studio.exe`.

---

## ⚖️ Aviso Legal / Disclaimer

O **CheatCraft Studio** foi desenvolvido exclusivamente para fins de estudo, aprendizado de engenharia reversa e uso em jogos **singleplayer offline**. Não utilize em jogos multiplayer ou títulos com anti-cheat online.
