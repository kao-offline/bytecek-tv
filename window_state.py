"""Reuse live browser windows without navigating them or discarding page state."""
import json
import hashlib
from urllib.parse import urlsplit
import os
import re
import subprocess
import threading
import time
from pathlib import Path

STATE = Path(os.environ.get('XDG_RUNTIME_DIR', str(Path.home()/'.local/state/bytecek'))) / f'bytecek-windows-{os.getuid() if hasattr(os,"getuid") else "test"}.json'
LOCK = threading.Lock()

def output(*args):
    try:
        return subprocess.check_output(args, stderr=subprocess.DEVNULL, timeout=2).decode().strip()
    except (OSError, subprocess.SubprocessError):
        return ''

def windows():
    return re.findall(r'0x[0-9a-fA-F]+', output('xprop','-root','_NET_CLIENT_LIST'))

def browser(window):
    cls=output('xprop','-id',window,'WM_CLASS').lower()
    return 'chromium' in cls or 'chrome' in cls

def activate(window):
    subprocess.run(['xdotool','windowmap',window,'windowactivate','--sync',window],check=False,timeout=3)

def load():
    try:
        data=json.loads(STATE.read_text())
        return data if isinstance(data,dict) else {}
    except (OSError,ValueError):
        return {}

def tagged(key,window):
    expected=hashlib.sha256(key.encode()).hexdigest()
    marker=output('xprop','-id',window,'_BYTECEK_TILE_KEY')
    if expected in marker:return True
    # Only migrate untagged windows whose browser/app role matches the tile.
    if not any(text in marker for text in ('not found','no such atom')):return False
    classes=re.findall(r'"([^"]+)"',output('xprop','-id',window,'WM_CLASS').lower())
    cls=classes[0] if classes else ''
    if key.startswith('app|'):
        host=urlsplit(key.split('|',1)[1]).hostname or ''
        matches=bool(host) and host.lower() in cls
    else:
        matches=cls.startswith('chromium (') or cls in ('chromium','google-chrome','google-chrome-stable')
    if matches:
        subprocess.run(['xprop','-id',window,'-f','_BYTECEK_TILE_KEY','8s','-set','_BYTECEK_TILE_KEY',expected],check=False,timeout=2)
    return matches

def remember(key,window):
    subprocess.run(['xprop','-id',window,'-f','_BYTECEK_TILE_KEY','8s','-set','_BYTECEK_TILE_KEY',hashlib.sha256(key.encode()).hexdigest()],check=False,timeout=2)
    state=load()
    state[key]={'window':window,'pid':output('xprop','-id',window,'_NET_WM_PID')}
    STATE.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    STATE.write_text(json.dumps(state))
    STATE.chmod(0o600)

def normal_window(window):
    # Let Chromium leave its own F11 mode so its tabs/address bar return too.
    if '_NET_WM_STATE_FULLSCREEN' in output('xprop','-id',window,'_NET_WM_STATE'):
        subprocess.run(['xdotool','windowactivate','--sync',window,'key','--clearmodifiers','F11'],check=False,timeout=3)
        time.sleep(.3)
    subprocess.run(['wmctrl','-ir',window,'-b','remove,fullscreen'],check=False,timeout=3)
    subprocess.run(['wmctrl','-ir',window,'-b','add,maximized_vert,maximized_horz'],check=False,timeout=3)

def launch(key,cmd,normal=False):
    with LOCK:
        entry=load().get(key,{})
        window=entry.get('window')
        if window in windows() and browser(window) and output('xprop','-id',window,'_NET_WM_PID')==entry.get('pid') and tagged(key,window):
            activate(window)
            if normal:normal_window(window)
            else:subprocess.run(['wmctrl','-ir',window,'-b','add,fullscreen'],check=False,timeout=3)
            return True
        before=set(windows())
        subprocess.Popen(cmd,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
        # Wait for the WM to register the new top-level window, not for site loading.
        for _ in range(50):
            fresh=[w for w in windows() if w not in before and browser(w)]
            if fresh:
                remember(key,fresh[-1])
                if normal:normal_window(fresh[-1])
                else:subprocess.run(['wmctrl','-ir',fresh[-1],'-b','add,fullscreen'],check=False,timeout=3)
                return False
            time.sleep(.1)
        return False
