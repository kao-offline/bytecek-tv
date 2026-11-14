"""Reuse live browser windows without navigating them or discarding page state."""
import json
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

def remember(key,window):
    state=load()
    state[key]={'window':window,'pid':output('xprop','-id',window,'_NET_WM_PID')}
    STATE.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    STATE.write_text(json.dumps(state))
    STATE.chmod(0o600)

def normal_window(window):
    subprocess.run(['wmctrl','-ir',window,'-b','remove,fullscreen'],check=False,timeout=3)
    subprocess.run(['wmctrl','-ir',window,'-b','add,maximized_vert,maximized_horz'],check=False,timeout=3)

def launch(key,cmd,normal=False):
    with LOCK:
        entry=load().get(key,{})
        window=entry.get('window')
        if window in windows() and browser(window) and output('xprop','-id',window,'_NET_WM_PID')==entry.get('pid'):
            activate(window)
            if normal:normal_window(window)
            return True
        before=set(windows())
        subprocess.Popen(cmd,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
        # Wait for the WM to register the new top-level window, not for site loading.
        for _ in range(50):
            fresh=[w for w in windows() if w not in before and browser(w)]
            if fresh:
                remember(key,fresh[-1])
                if normal:normal_window(fresh[-1])
                return False
            time.sleep(.1)
        return False
