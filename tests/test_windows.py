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
            with patch.object(window_state,'STATE',state), patch.object(window_state,'windows',return_value=['0x123']), patch.object(window_state,'browser',return_value=True), patch.object(window_state,'belongs',return_value=True), patch.object(window_state,'output',return_value='pid=42'), patch.object(window_state,'tagged',return_value=True), patch.object(window_state.subprocess,'run'), patch.object(window_state,'activate') as activate, patch.object(window_state.subprocess,'Popen') as spawn:
                self.assertTrue(window_state.launch('app|url',['chromium','url']))
                activate.assert_called_once_with('0x123')
                spawn.assert_not_called()

    def test_recycled_window_id_does_not_resume_another_process(self):
        with patch.object(window_state,'load',return_value={'app|url':{'window':'0x123','pid':'pid=42'}}), patch.object(window_state,'windows',return_value=['0x123']), patch.object(window_state,'browser',return_value=True), patch.object(window_state,'belongs',return_value=True), patch.object(window_state,'output',return_value='pid=99'), patch.object(window_state,'tagged',return_value=True), patch.object(window_state.subprocess,'run'), patch.object(window_state,'activate') as activate, patch.object(window_state.subprocess,'Popen') as spawn, patch.object(window_state.time,'sleep'):
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

    def test_service_mode_never_fullscreens_apps(self):
        with patch.object(window_state,'service_enabled',return_value=True), patch.object(window_state.subprocess,'run') as run:
            window_state.apply_app_mode('0x123')
            commands=[call.args[0] for call in run.call_args_list]
            self.assertIn(['wmctrl','-ir','0x123','-b','remove,fullscreen'],commands)
            self.assertNotIn(['wmctrl','-ir','0x123','-b','add,fullscreen'],commands)
            self.assertFalse(any(command[0]=='xdotool' for command in commands))

    def test_tv_mode_restores_app_fullscreen(self):
        with patch.object(window_state,'service_enabled',return_value=False), patch.object(window_state.subprocess,'run') as run:
            window_state.apply_app_mode('0x123')
            run.assert_called_once_with(['wmctrl','-ir','0x123','-b','add,fullscreen'],check=False,timeout=3)

    def test_home_window_is_never_an_app(self):
        home='WM_CLASS(STRING) = "chromium (/home/tvbox/.config/bytecek-launcher)", "Chromium"'
        with patch.object(window_state,'output',return_value=home):
            self.assertFalse(window_state.browser('0x1'))
            self.assertFalse(window_state.belongs('app|https://spilled.kaooffline.top/','0x1'))

    def test_window_must_match_the_tile(self):
        spilled='WM_CLASS(STRING) = "spilled.kaooffline.top", "Chromium"'
        with patch.object(window_state,'output',return_value=spilled):
            self.assertTrue(window_state.belongs('app|https://spilled.kaooffline.top/','0x2'))
            self.assertFalse(window_state.belongs('app|https://www.seznam.cz','0x2'))
            self.assertFalse(window_state.belongs('browser|https://www.google.com/','0x2'))

    def test_preload_ignores_other_new_windows(self):
        # Home appears first while Spilled is still starting: only Spilled may be recorded.
        new=[[],[],['0x9'],['0x9','0x5']]  # existing check, before, Home appears, then Spilled
        def wins():
            return new.pop(0) if new else ['0x9','0x5']
        classes={'0x9':'"chromium (/home/tvbox/.config/bytecek-launcher)", "Chromium"','0x5':'"spilled.kaooffline.top", "Chromium"'}
        def out(*args):
            if args[0]=='xprop' and args[-1]=='WM_CLASS':return 'WM_CLASS(STRING) = '+classes[args[2]]
            if args[0]=='xprop' and args[-1]=='WM_STATE':return 'window state: Iconic'
            return ''
        with patch.object(window_state,'load',return_value={}), patch.object(window_state,'windows',side_effect=lambda:wins()), patch.object(window_state,'output',side_effect=out), patch.object(window_state,'remember') as remember, patch.object(window_state.subprocess,'run'), patch.object(window_state.subprocess,'Popen'), patch.object(window_state.time,'sleep'):
            self.assertTrue(window_state.preload('app|https://spilled.kaooffline.top/',['chromium']))
            remember.assert_called_once_with('app|https://spilled.kaooffline.top/','0x5')

if __name__=='__main__':unittest.main()
