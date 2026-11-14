"""Window reuse must preserve the existing page rather than relaunch a URL."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import window_state

class WindowReuseTest(unittest.TestCase):
    def test_existing_page_is_activated_without_launch(self):
        with tempfile.TemporaryDirectory() as directory:
            state=Path(directory)/'windows.json'
            state.write_text(json.dumps({'app|url':{'window':'0x123','pid':'pid=42'}}))
            with patch.object(window_state,'STATE',state), patch.object(window_state,'windows',return_value=['0x123']), patch.object(window_state,'browser',return_value=True), patch.object(window_state,'output',return_value='pid=42'), patch.object(window_state,'tagged',return_value=True), patch.object(window_state.subprocess,'run'), patch.object(window_state,'activate') as activate, patch.object(window_state.subprocess,'Popen') as spawn:
                self.assertTrue(window_state.launch('app|url',['chromium','url']))
                activate.assert_called_once_with('0x123')
                spawn.assert_not_called()

    def test_recycled_window_id_does_not_resume_another_process(self):
        with patch.object(window_state,'load',return_value={'app|url':{'window':'0x123','pid':'pid=42'}}), patch.object(window_state,'windows',return_value=['0x123']), patch.object(window_state,'browser',return_value=True), patch.object(window_state,'output',return_value='pid=99'), patch.object(window_state,'tagged',return_value=True), patch.object(window_state.subprocess,'run'), patch.object(window_state,'activate') as activate, patch.object(window_state.subprocess,'Popen') as spawn, patch.object(window_state.time,'sleep'):
            self.assertFalse(window_state.launch('app|url',['chromium','url']))
            activate.assert_not_called()
            spawn.assert_called_once()

    def test_different_tile_marker_rejects_reused_id(self):
        with patch.object(window_state,'output',return_value='_BYTECEK_TILE_KEY(STRING) = "other-tile"'):
            self.assertFalse(window_state.tagged('browser|url','0x123'))

    def test_browser_tile_does_not_migrate_app_window(self):
        with patch.object(window_state,'output',side_effect=['_BYTECEK_TILE_KEY: not found.','WM_CLASS(STRING) = "spilled.kaooffline.top", "Chromium"']):
            self.assertFalse(window_state.tagged('browser|url','0x123'))

    def test_browser_exits_internal_fullscreen_before_maximizing(self):
        with patch.object(window_state,'output',return_value='_NET_WM_STATE_FULLSCREEN'), patch.object(window_state.subprocess,'run') as run, patch.object(window_state.time,'sleep'):
            window_state.normal_window('0x123')
            commands=[call.args[0] for call in run.call_args_list]
            self.assertEqual(commands[0],['xdotool','windowactivate','--sync','0x123','key','--clearmodifiers','F11'])
            self.assertEqual(commands[-1],['wmctrl','-ir','0x123','-b','add,maximized_vert,maximized_horz'])

if __name__=='__main__':unittest.main()
