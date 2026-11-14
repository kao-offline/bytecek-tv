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

UID = os.getuid() if hasattr(os,'getuid') else 'test'
RUNTIME = Path(os.environ.get('XDG_RUNTIME_DIR',f'/run/user/{UID}'))
if not RUNTIME.is_dir():RUNTIME=Path.home()/'.local/state/bytecek'
STATE = RUNTIME / f'bytecek-windows-{UID}.json'
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

def repaint(window):
    # Chromium may leave a window restored from minimized unpainted (the screen keeps
    # showing Home). Dropping fullscreen/maximize for a moment forces a fresh frame;
    # the mode functions below put it back.
    subprocess.run(['wmctrl','-ir',window,'-b','remove,fullscreen'],check=False,timeout=3)
    subprocess.run(['wmctrl','-ir',window,'-b','remove,maximized_vert,maximized_horz'],check=False,timeout=3)
    time.sleep(.05)

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

SERVICE = STATE.with_name('bytecek-service-mode')

def service_enabled():
    return SERVICE.exists()

def apply_app_mode(window):
    if service_enabled():
        subprocess.run(['wmctrl','-ir',window,'-b','remove,fullscreen'],check=False,timeout=3)
        subprocess.run(['wmctrl','-ir',window,'-b','remove,maximized_vert,maximized_horz'],check=False,timeout=3)
        subprocess.run(['wmctrl','-ir',window,'-e','0,80,80,1280,850'],check=False,timeout=3)
    else:
        subprocess.run(['wmctrl','-ir',window,'-b','add,fullscreen'],check=False,timeout=3)

def set_service_mode(enabled):
    SERVICE.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    if enabled:
        SERVICE.touch(mode=0o600)
    else:
        SERVICE.unlink(missing_ok=True)
    live=windows()
    for key,entry in load().items():
        window=entry.get('window')
        if key.startswith('app|') and window in live and browser(window) and output('xprop','-id',window,'_NET_WM_PID')==entry.get('pid') and tagged(key,window):
            apply_app_mode(window)
    return enabled

def launch(key,cmd,normal=False):
    with LOCK:
        entry=load().get(key,{})
        window=entry.get('window')
        if window in windows() and browser(window) and output('xprop','-id',window,'_NET_WM_PID')==entry.get('pid') and tagged(key,window):
            activate(window)
            repaint(window)
            if normal:normal_window(window)
            else:apply_app_mode(window)
            return True
        before=set(windows())
        subprocess.Popen(cmd,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
        # Wait for the WM to register the new top-level window, not for site loading.
        for _ in range(50):
            fresh=[w for w in windows() if w not in before and browser(w)]
            if fresh:
                remember(key,fresh[-1])
                if normal:normal_window(fresh[-1])
                else:apply_app_mode(fresh[-1])
                return False
            time.sleep(.1)
        return False

def preload(key,cmd):
    """Start an app window in the background (minimized) unless it is already open."""
    with LOCK:
        entry=load().get(key,{})
        window=entry.get('window')
        if window in windows() and browser(window):
            return False
        before=set(windows())
        subprocess.Popen(cmd,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
        for _ in range(600):  # a cold start at boot can take a while
            fresh=[w for w in windows() if w not in before and browser(w)]
            if fresh:
                window=fresh[-1]
                remember(key,window)
                # The WM may not manage the window yet; retry until it is really iconic.
                for _ in range(40):
                    subprocess.run(['xdotool','windowminimize',window],check=False,timeout=3)
                    time.sleep(.25)
                    if 'Iconic' in output('xprop','-id',window,'WM_STATE'):
                        break
                # Give focus back to Home if it is already on screen.
                home=output('xdotool','search','--name','^Bytecek Launcher( - .*)?$').split()
                if home:
                    subprocess.run(['xdotool','windowactivate',home[-1]],check=False,timeout=3)
                return True
            time.sleep(.1)
        return False
