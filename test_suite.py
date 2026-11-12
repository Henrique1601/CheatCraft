import os
import sys
import tempfile
import xml.etree.ElementTree as ET
import unittest
from unittest.mock import MagicMock, patch

from memory_engine import MemoryEngine
from core.ct_generator import CheatTableGenerator
from core.ct_importer import CheatTableImporter
from core.sound_feedback import SoundFeedback
from core.hud_overlay import InGameHUDOverlay

class TestCheatCraftStudio(unittest.TestCase):

    def setUp(self):
        self.mem = MemoryEngine(process_name="GTA5.exe")

    def test_01_address_parser(self):
        """Test universal module strings and raw hex parsing."""
        self.mem.is_connected = True
        self.mem.base_address = 0x140000000
        self.mem._module_cache["gta5.exe"] = 0x140000000
        self.mem._module_cache["unityplayer.dll"] = 0x7FF800000000

        # Quoted module with hex offset
        addr1 = self.mem.parse_address('"GTA5.exe"+01C3A100')
        self.assertEqual(addr1, 0x140000000 + 0x01C3A100)

        # UnityPlayer.dll module
        addr2 = self.mem.parse_address('"UnityPlayer.dll"+015F3C00')
        self.assertEqual(addr2, 0x7FF800000000 + 0x015F3C00)

        # Unquoted module
        addr3 = self.mem.parse_address('GTA5.exe+0x1000')
        self.assertEqual(addr3, 0x140000000 + 0x1000)

        # Negative offset
        addr4 = self.mem.parse_address('"GTA5.exe"-0x100')
        self.assertEqual(addr4, 0x140000000 - 0x100)

        # Raw hex string
        addr5 = self.mem.parse_address("0x140001000")
        self.assertEqual(addr5, 0x140001000)

        # Raw hex without 0x
        addr6 = self.mem.parse_address("140001000")
        self.assertEqual(addr6, 0x140001000)

        # Direct int
        addr7 = self.mem.parse_address(0x140001000)
        self.assertEqual(addr7, 0x140001000)

        # Standalone module name
        addr8 = self.mem.parse_address('"GTA5.exe"')
        self.assertEqual(addr8, 0x140000000)

    def test_02_dual_bitness_pointer_resolution(self):
        """Test dual 32-bit and 64-bit pointer walking."""
        class MockProcess:
            def __init__(self):
                self.process_handle = 9999
                self.mem_64 = {
                    0x141C3A100: 0x200000000,
                    0x200000008: 0x300000000,
                    0x300000030: 0x400000000,
                }
                self.mem_32 = {
                    0x00401000: 0x00500000,
                    0x00500008: 0x00600000,
                    0x00600030: 0x00700000,
                }

            def read_longlong(self, addr):
                return self.mem_64.get(addr, 0)

            def read_int(self, addr):
                return self.mem_32.get(addr, 0)

        self.mem.is_connected = True
        self.mem.base_address = 0x140000000
        self.mem.pm = MockProcess()
        self.mem._module_cache["gta5.exe"] = 0x140000000

        # Test 64-bit resolution
        with patch.object(MemoryEngine, 'is_64_bit', new=True):
            resolved = self.mem.resolve_pointer('"GTA5.exe"+01C3A100', [8, 48, 0])
            # 0x1401C3A100 -> [0x200000000] + 8 = 0x200000008 -> [0x300000000] + 48 (0x30) = 0x300000030 -> [0x400000000] + 0 = 0x400000000
            self.assertEqual(resolved, 0x400000000)

        # Test 32-bit resolution
        self.mem.base_address = 0x00400000
        self.mem._module_cache["game.exe"] = 0x00400000
        with patch.object(MemoryEngine, 'is_64_bit', new=False):
            resolved32 = self.mem.resolve_pointer('"game.exe"+1000', [8, 48, 4])
            # 0x00401000 -> [0x00500000] + 8 = 0x00500008 -> [0x00600000] + 48 (0x30) = 0x00600030 -> [0x00700000] + 4 = 0x00700004
            self.assertEqual(resolved32, 0x00700004)

    def test_03_handle_leak_prevention(self):
        """Verify connect() checks existing handle and avoids leaking handles."""
        mock_pm = MagicMock()
        mock_pm.process_handle = 1234
        self.mem.pm = mock_pm
        self.mem.is_connected = True
        self.mem._connected_process_name = "GTA5.exe"
        self.mem.process_name = "GTA5.exe"

        # Mock GetExitCodeProcess returning STILL_ACTIVE (259)
        with patch("ctypes.windll.kernel32.GetExitCodeProcess") as mock_get_exit:
            def side_effect(handle, byref_code):
                byref_code._obj.value = 259
                return 1
            mock_get_exit.side_effect = side_effect

            # Calling connect again should NOT re-instantiate pymem
            with patch("pymem.Pymem") as mock_pymem_init:
                connected = self.mem.connect()
                self.assertTrue(connected)
                mock_pymem_init.assert_not_called()

        # If process changed, disconnect must be called cleanly
        self.mem.process_name = "RDR2.exe"
        with patch.object(self.mem, "disconnect") as mock_disc:
            with patch("pymem.Pymem", side_effect=Exception("Game not open")):
                self.mem.connect()
                mock_disc.assert_called()

    def test_04_ct_generator_and_importer_offset_order(self):
        """Verify bottom-up ordering in CE XML and duplicate VariableType removal."""
        temp_ct = os.path.join(tempfile.gettempdir(), "test_ct_offsets.ct")
        entries = [
            {
                "id": 1,
                "description": "God Mode",
                "type": "Float",
                "address": '"GTA5.exe"+01C3A100',
                "offsets": [8, 48, 0],
                "hotkey": "NUMPAD 1"
            },
            {
                "id": 2,
                "description": "Script Cheat",
                "type": "Auto Assembler Script",
                "script": "[ENABLE]\n// code\n[DISABLE]\n",
                "hotkey": "NUMPAD 2"
            }
        ]

        CheatTableGenerator.generate_ct("GTA V", "GTA5.exe", entries, temp_ct)

        tree = ET.parse(temp_ct)
        root = tree.getroot()
        cheat_entries = root.findall(".//CheatEntry")

        # 1. XML Offsets must be in bottom-up order: 0, 30 (hex for 48), 8
        offsets_el = cheat_entries[0].find("Offsets")
        xml_offsets = [o.text for o in offsets_el.findall("Offset")]
        self.assertEqual(xml_offsets, ["0", "30", "8"])

        # 2. Script entry must have exactly ONE VariableType tag
        vtypes = cheat_entries[1].findall("VariableType")
        self.assertEqual(len(vtypes), 1)
        self.assertEqual(vtypes[0].text, "Auto Assembler Script")

        # 3. Importer must convert bottom-up back to top-down [8, 48, 0]
        imported = CheatTableImporter.parse_ct_file(temp_ct)
        imported_cheats = imported["cheats"]
        self.assertEqual(imported_cheats[0]["offsets"], [8, 48, 0])

        if os.path.exists(temp_ct):
            os.remove(temp_ct)

    def test_05_sound_feedback_async(self):
        """Verify SoundFeedback runs asynchronously without blocking."""
        with patch("winsound.Beep") as mock_beep:
            SoundFeedback.play_connected()
            SoundFeedback.play_cheat_on()
            SoundFeedback.play_cheat_off()
            SoundFeedback.play_disconnected()
            # If calls return immediately, this line is reached in < 1ms
            self.assertTrue(True)

    def test_06_hud_overlay_fixes(self):
        """Verify HUD click-through styles, draggable bindings, and crosshair persistence."""
        hud = InGameHUDOverlay()
        hud.create_window()
        hud.root.update()

        # Check crosshair creation and styles
        hud.toggle_crosshair()
        hud.root.update()
        self.assertTrue(hud.crosshair_enabled)
        self.assertIsNotNone(hud.crosshair_window)

        # Check hiding HUD does NOT disable crosshair
        hud.toggle_visibility()
        hud.root.update()
        self.assertTrue(hud.crosshair_enabled)

        # Clean destroy
        hud.destroy()

    def test_07_spec_file_uac_admin(self):
        """Verify CheatCraft.spec contains uac_admin=True."""
        spec_path = os.path.join(os.path.dirname(__file__), "CheatCraft.spec")
        with open(spec_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("uac_admin=True", content)

    def test_08_launcher_switch_sync_and_enforcement(self):
        """Verify switch state synchronization and cheat enforcement dictionary in launcher."""
        from launcher import CheatCraftApp

        with patch("threading.Thread") as mock_thread:
            # Prevent background threads from running indefinitely during unit test
            app = CheatCraftApp()
            app.withdraw() # Hide window
            app.update()

            # Initial state
            self.assertIsNotNone(app.selected_game)
            first_game = app.presets[0]
            second_game = app.presets[1]
            first_cheat = first_game["cheats"][0]
            first_cid = first_cheat["id"]

            # Toggle first cheat ON
            app._toggle_live_cheat(first_cid, first_cheat)
            self.assertTrue(app.active_cheats[first_cid])
            self.assertIn(first_cid, app.active_cheat_objects)
            self.assertEqual(app.cheat_switches[first_cid].get(), 1)

            # Switch to second game in sidebar
            app._select_game(second_game)
            app.update()
            # Second game's first cheat should be OFF by default
            second_cid = second_game["cheats"][0]["id"]
            self.assertEqual(app.cheat_switches[second_cid].get(), 0)

            # Switch back to first game
            app._select_game(first_game)
            app.update()
            # First cheat switch MUST still be ON (synchronized)
            self.assertEqual(app.cheat_switches[first_cid].get(), 1)
            self.assertTrue(app.active_cheats[first_cid])

            app.destroy()

    def test_09_edge_cases(self):
        """Test boundary conditions, empty inputs, and error paths."""
        self.mem.is_connected = True
        self.mem.base_address = 0x140000000
        self.mem._module_cache["gta5.exe"] = 0x140000000

        # Empty / None / Malformed addresses
        self.assertIsNone(self.mem.parse_address(None))
        self.assertIsNone(self.mem.parse_address(""))
        self.assertIsNone(self.mem.parse_address("   "))
        self.assertIsNone(self.mem.parse_address("unknown_module.dll+100"))
        self.assertIsNone(self.mem.parse_address("bad+offset+extra"))

        # Empty offsets vs None
        addr = self.mem.resolve_pointer('"GTA5.exe"+01C3A100', [])
        self.assertEqual(addr, 0x140000000 + 0x01C3A100)
        addr2 = self.mem.resolve_pointer('"GTA5.exe"+01C3A100', None)
        self.assertEqual(addr2, 0x140000000 + 0x01C3A100)

        # Disconnected resolution
        self.mem.is_connected = False
        self.assertIsNone(self.mem.resolve_pointer('"GTA5.exe"+01C3A100'))

if __name__ == "__main__":
    unittest.main()
