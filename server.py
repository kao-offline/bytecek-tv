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
from urllib.parse import urlsplit

HOST = '127.0.0.1'
PORT = 8765
UI = Path(__file__).resolve().parent / 'ui'
TOKEN = secrets.token_urlsafe(32)
BROWSER = shutil.which('google-chrome-stable') or shutil.which('google-chrome') or shutil.which('chromium')
MIMES = {'.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8','.js':'text/javascript; charset=utf-8','.svg':'image/svg+xml','.png':'image/png'}


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
            self.reply_json(200,{'token':TOKEN})
            return
        if path == '/':
            path = '/index.html'
        allowed = {'/index.html','/style.css','/app.js','/b.svg'}
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

    def do_POST(self):
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

        if self.path == '/api/launch':
            url = body.get('url')
            mode = body.get('mode')
            if not valid_web_url(url) or mode not in ('app','browser'):
                self.reply_json(400,{'error':'Invalid web shortcut'})
                return
            if not BROWSER:
                self.reply_json(500,{'error':'Chromium/Chrome is missing'})
                return
            cmd = [BROWSER,'--user-data-dir='+str(Path.home()/'.config/bytecek-sites'),'--password-store=basic','--force-dark-mode','--force-prefers-reduced-motion=reduce','--load-extension=/opt/bytecek/browser-extension','--no-first-run','--no-default-browser-check','--disable-session-crashed-bubble']
            if mode == 'app':
                cmd += [f'--app={url}','--start-fullscreen']
            else:
                cmd += ['--new-window','--start-fullscreen',url]
            try:
                subprocess.Popen(cmd,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
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
                subprocess.run(['xdotool','search','--name','Bytecek Launcher','windowclose'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False)
            threading.Thread(target=exit_launcher,daemon=True).start()
            return
        self.reply_json(404,{'error':'Unknown action'})


def main():
    print(f'Bytecek server listening on http://{HOST}:{PORT}',flush=True)
    httpd = ThreadingHTTPServer((HOST,PORT),Handler)
    httpd.serve_forever(poll_interval=.3)

if __name__ == '__main__':
    main()
