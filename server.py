#!/usr/bin/env python3
"""Loopback-only Bytecek launcher service. No third-party Python packages."""
import json
import os
import secrets
import shutil
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, urlsplit
import window_state

HOST = '127.0.0.1'
PORT = 8765
UI = Path(__file__).resolve().parent / 'ui'
TOKEN = secrets.token_urlsafe(32)
BROWSER = shutil.which('google-chrome-stable') or shutil.which('google-chrome') or shutil.which('chromium')
MIMES = {'.ttf':'font/ttf','.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8','.js':'text/javascript; charset=utf-8','.svg':'image/svg+xml','.png':'image/png'}
SPILLED_ORIGIN = 'https://spilled.kaooffline.top'
SPILLED_HOME = SPILLED_ORIGIN + '/'
STATE_DIR = Path(os.environ.get('XDG_STATE_HOME', Path.home()/'.local/state')) / 'bytecek'
CONTINUE_FILE = STATE_DIR / 'continue-watching.json'
PENDING = {'url':None,'at':0.0}
PENDING_LOCK = threading.Lock()


def clean_text(value, limit):
    return value.strip()[:limit] if isinstance(value, str) else ''


def clean_continue(items):
    """Accept only display fields; episode links are rebuilt here, never taken from the sender."""
    if not isinstance(items, list):
        raise ValueError('items must be a list')
    result = []
    for item in items[:12]:
        if not isinstance(item, dict):
            continue
        episode = clean_text(item.get('id'), 160)
        show = clean_text(item.get('show'), 120)
        if not episode or not show:
            continue
        image = item.get('image')
        image = image if isinstance(image, str) and image.startswith('https://') and valid_web_url(image) else ''
        progress = item.get('progress')
        progress = max(0, min(100, int(progress))) if isinstance(progress, (int, float)) and progress == progress else 0
        result.append({'id':episode,'show':show,'label':clean_text(item.get('label'),120),'left':clean_text(item.get('left'),40),
                       'image':image,'progress':progress,'url':f'{SPILLED_ORIGIN}/library/watch/{quote(episode, safe="")}'})
    return result


def read_continue():
    try:
        data = json.loads(CONTINUE_FILE.read_text(encoding='utf-8'))
        return {'items':clean_continue(data.get('items',[])),'updatedAt':data.get('updatedAt',0)}
    except (OSError, ValueError, AttributeError):
        return {'items':[],'updatedAt':0}


def write_continue(items):
    STATE_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    tmp = CONTINUE_FILE.with_suffix('.tmp')
    tmp.write_text(json.dumps({'items':items,'updatedAt':int(time.time())}), encoding='utf-8')
    tmp.replace(CONTINUE_FILE)


def spilled_episode(url):
    parts = urlsplit(url)
    return f'{parts.scheme}://{parts.hostname}' == SPILLED_ORIGIN and parts.path.startswith('/library/watch/')


def valid_web_url(value):
    if not isinstance(value, str) or len(value) > 2048:
        return False
    try:
        url = urlsplit(value)
        return url.scheme in ('http', 'https') and bool(url.hostname) and not url.username and not url.password
    except ValueError:
        return False


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print('[Bytecek]', fmt % args, flush=True)

    def reply_json(self, code, obj):
        payload = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Length',str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        path = self.path.split('?',1)[0]
        if path == '/api/config':
            self.reply_json(200,{'token':TOKEN,'service':window_state.service_enabled()})
            return
        if path == '/api/continue':
            self.reply_json(200,read_continue())
            return
        if path == '/':
            path = '/index.html'
        allowed = {'/index.html','/style.css','/app.js','/b.svg','/fonts/BigShouldersDisplay.ttf'}
        if path not in allowed and path not in {'/icons/spilled.png','/icons/ct24.svg','/icons/chrome.svg'}:
            self.send_error(404)
            return
        file = UI / path[1:]
        if not file.is_file():
            self.send_error(404)
            return
        payload = file.read_bytes()
        self.send_response(200)
        self.send_header('Content-Type',MIMES.get(file.suffix,'application/octet-stream'))
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Cache-Control','no-store')
        self.send_header('Content-Length',str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def extension_request(self):
        """The Bytecek browser extension reports Spilled progress and picks up episode jumps."""
        try:
            count = int(self.headers.get('Content-Length','0'))
            if not 0 < count <= 65536:
                raise ValueError
            body = json.loads(self.rfile.read(count))
            if not isinstance(body, dict):
                raise ValueError
        except ValueError:
            self.reply_json(400,{'error':'Invalid request'})
            return
        if self.path == '/api/spilled/continue':
            try:
                items = clean_continue(body.get('items'))
            except ValueError:
                self.reply_json(400,{'error':'Invalid items'})
                return
            write_continue(items)
            self.reply_json(200,{'ok':True,'count':len(items)})
            return
        if self.path == '/api/spilled/pending':
            with PENDING_LOCK:
                url = PENDING['url'] if time.time() - PENDING['at'] < 20 else None
                PENDING['url'] = None
            self.reply_json(200,{'url':url} if url else {})
            return
        self.reply_json(404,{'error':'Unknown action'})

    def do_POST(self):
        if self.path.startswith('/api/spilled/') and (self.headers.get('Origin') or '').startswith('chrome-extension://'):
            self.extension_request()
            return
        if self.headers.get('X-Bytecek-Token') != TOKEN or self.headers.get('Origin') != f'http://{HOST}:{PORT}':
            self.reply_json(403,{'error':'Unauthorized request'})
            return
        try:
            count = int(self.headers.get('Content-Length','0'))
            if not 0 < count <= 4096:
                raise ValueError('Invalid request size')
            body = json.loads(self.rfile.read(count))
            if not isinstance(body, dict):
                raise ValueError('Invalid JSON payload')
        except (ValueError,json.JSONDecodeError):
            self.reply_json(400,{'error':'Invalid request'})
            return

        if self.path == '/api/service':
            enabled=body.get('enabled')
            if not isinstance(enabled,bool):
                self.reply_json(400,{'error':'Service mode must be true or false'})
                return
            window_state.set_service_mode(enabled)
            self.reply_json(200,{'ok':True,'service':enabled})
            return

        if self.path == '/api/launch':
            url = body.get('url')
            mode = body.get('mode')
            if not valid_web_url(url) or mode not in ('app','browser'):
                self.reply_json(400,{'error':'Invalid web shortcut'})
                return
            if not BROWSER:
                self.reply_json(500,{'error':'Chromium/Chrome is missing'})
                return
            cmd = [BROWSER,'--user-data-dir='+str(Path.home()/'.config/bytecek-sites'),'--password-store=basic','--use-gl=angle','--use-angle=gl','--enable-native-gpu-memory-buffers','--enable-zero-copy','--enable-features=AcceleratedVideoDecodeLinuxGL,AcceleratedVideoDecodeLinuxZeroCopyGL','--force-dark-mode','--force-prefers-reduced-motion=reduce','--load-extension=/opt/bytecek/browser-extension','--no-first-run','--no-default-browser-check','--disable-session-crashed-bubble']
            key = mode+'|'+url
            episode = mode == 'app' and spilled_episode(url)
            if episode:
                # Reuse the open Spilled window; the extension moves it to the episode.
                key = 'app|'+SPILLED_HOME
                with PENDING_LOCK:
                    PENDING.update(url=url, at=time.time())
            if mode == 'app':
                cmd += [f'--app={url}']
            else:
                cmd += ['--new-window','--start-maximized','chrome://newtab/']
            try:
                reused = window_state.launch(key,cmd,normal=mode=='browser')
                if episode and not reused:
                    with PENDING_LOCK:
                        PENDING['url'] = None
            except OSError as error:
                self.reply_json(500,{'error':str(error)})
                return
            self.reply_json(200,{'ok':True})
            return

        if self.path == '/api/power':
            action = body.get('action')
            if action not in ('poweroff','reboot','suspend'):
                self.reply_json(400,{'error':'Invalid power action'})
                return
            try:
                subprocess.Popen(['sudo','-n','/usr/local/sbin/bytecek-power',action],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
            except OSError as error:
                self.reply_json(500,{'error':str(error)})
                return
            self.reply_json(200,{'ok':True})
            return

        if self.path == '/api/exit':
            self.reply_json(200,{'ok':True})
            # Give browser time to receive the response before closing it.
            def exit_launcher():
                time.sleep(.3)
                subprocess.run(['xdotool','search','--name','Bytecek Launcher','windowminimize'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False)
            threading.Thread(target=exit_launcher,daemon=True).start()
            return
        self.reply_json(404,{'error':'Unknown action'})


def main():
    print(f'Bytecek server listening on http://{HOST}:{PORT}',flush=True)
    httpd = ThreadingHTTPServer((HOST,PORT),Handler)
    httpd.serve_forever(poll_interval=.3)

if __name__ == '__main__':
    main()
