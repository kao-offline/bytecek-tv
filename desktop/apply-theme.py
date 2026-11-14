#!/usr/bin/env python3
"""Lightly theme the LXQt desktop of the TV account in the Bytecek look.

Edits only the listed keys (the user's other settings are kept) and is safe to
run repeatedly. Run as the TV user."""
import re
from pathlib import Path

HOME = Path.home()
CONF = HOME / '.config'


def ini_set(path, values):
    """values: {section: {key: value}}; QSettings-compatible line edit."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = path.read_text(encoding='utf-8').splitlines() if path.exists() else []
    for section, pairs in values.items():
        head = f'[{section}]'
        if head not in lines:
            if lines and lines[-1].strip():
                lines.append('')
            lines.append(head)
        start = lines.index(head) + 1
        end = next((i for i in range(start, len(lines)) if lines[i].startswith('[')), len(lines))
        for key, value in pairs.items():
            pattern = re.compile(rf'^{re.escape(key)}\s*=')
            for i in range(start, end):
                if pattern.match(lines[i]):
                    lines[i] = f'{key}={value}'
                    break
            else:
                insert = end
                while insert > start and not lines[insert - 1].strip():
                    insert -= 1
                lines.insert(insert, f'{key}={value}')
                end += 1
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


# Panel: taller, bigger icons, oxblood with cream text.
ini_set(CONF / 'lxqt/panel.conf', {
    'panel1': {'panelSize': '56', 'iconSize': '36', 'background-color': '#1a0b0d',
               'font-color': '#f6e9cc', 'opacity': '96'},
    'taskbar': {'buttonWidth': '280'},
    'mainmenu': {'icon': '/opt/bytecek/boot/b-large.png', 'ownIcon': 'true'},
})
# Qt apps (file manager, settings): dark theme tinted to the launcher palette, larger font.
ini_set(CONF / 'lxqt/lxqt.conf', {
    'General': {'theme': 'dark', 'icon_theme': 'Papirus-Dark'},
    'Qt': {'style': 'Fusion', 'font': '"DejaVu Sans,12,-1,5,50,0,0,0,0,0"'},
    'Palette': {'window_color': '#24120f', 'window_text_color': '#f6e9cc', 'base_color': '#160a0b',
                'text_color': '#f6e9cc', 'highlight_color': '#b3262b', 'highlighted_text_color': '#ffffff',
                'link_color': '#ffd98c', 'link_visited_color': '#d9b26a'},
})
# Desktop: Bytecek wallpaper, bigger icons, launch the Bytecek TV icon without a prompt.
ini_set(CONF / 'pcmanfm-qt/lxqt/settings.conf', {
    'Behavior': {'QuickExec': 'true'},
    'Desktop': {'Wallpaper': '/opt/bytecek/desktop/wallpaper.svg', 'WallpaperMode': 'zoom',
                'DesktopIconSize': '80', 'FgColor': '#f6e9cc', 'ShadowColor': '#000000',
                'Font': '"DejaVu Sans,14,-1,5,50,0,0,0,0,0"'},
})
# Openbox for desktop mode: system defaults + Bytecek theme + large title font (= large buttons).
rc = Path('/etc/xdg/openbox/rc.xml').read_text(encoding='utf-8')
rc = re.sub(r'<name>[^<]*</name>(\s*<titleLayout>)NLIMC', r'<name>Bytecek</name>\1LIMC', rc, count=1)
rc = re.sub(r'(<font place="(?:Active|Inactive)Window">\s*<name>)sans(</name>\s*<size>)\d+', r'\1DejaVu Sans\g<2>19', rc)
rc = re.sub(r'(<font place="Menu(?:Header|Item)">\s*<name>)sans(</name>\s*<size>)\d+', r'\1DejaVu Sans\g<2>16', rc)
(CONF / 'bytecek').mkdir(parents=True, exist_ok=True)
(CONF / 'bytecek/openbox-desktop.xml').write_text(rc, encoding='utf-8')
print('Bytecek desktop theme applied')
