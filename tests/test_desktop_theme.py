#!/usr/bin/env python3
"""apply-theme.py edits only its keys, keeps user settings, and is idempotent."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RC = '''<theme>
  <name>Clearlooks</name>
  <titleLayout>NLIMC</titleLayout>
  <font place="ActiveWindow">
    <name>sans</name>
    <size>8</size>
  </font>
  <font place="MenuItem">
    <name>sans</name>
    <size>9</size>
  </font>
</theme>
'''


class ThemeTest(unittest.TestCase):
    def run_apply(self, home, rc):
        src = (ROOT / 'desktop/apply-theme.py').read_text(encoding='utf-8')
        src = src.replace("Path('/etc/xdg/openbox/rc.xml')", f"Path({str(rc)!r})")
        env = dict(os.environ, HOME=str(home), USERPROFILE=str(home))
        subprocess.run([sys.executable, '-c', src], env=env, check=True, capture_output=True)

    def test_apply(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            rc = home / 'rc.xml'
            rc.write_text(RC)
            panel = home / '.config/lxqt/panel.conf'
            panel.parent.mkdir(parents=True)
            panel.write_text('[General]\n__userfile__=true\n\n[panel1]\nalignment=-1\niconSize=22\npanelSize=32\nposition=Bottom\n\n[quicklaunch]\nalignment=Left\n')
            self.run_apply(home, rc)
            first = panel.read_text()
            self.run_apply(home, rc)
            self.assertEqual(first, panel.read_text())  # idempotent
            self.assertIn('panelSize=56', first)
            self.assertIn('position=Bottom', first)  # user setting kept
            self.assertIn('[quicklaunch]\nalignment=Left', first)
            self.assertEqual(first.count('panelSize='), 1)
            pcm = (home / '.config/pcmanfm-qt/lxqt/settings.conf').read_text()
            self.assertIn('QuickExec=true', pcm)
            ob = (home / '.config/bytecek/openbox-desktop.xml').read_text()
            self.assertIn('<name>Bytecek</name>', ob)
            self.assertIn('<titleLayout>LIMC', ob)
            self.assertIn('<size>15</size>', ob)
            self.assertIn('<size>13</size>', ob)


if __name__ == '__main__':
    unittest.main()
