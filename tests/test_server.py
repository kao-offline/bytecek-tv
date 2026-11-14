#!/usr/bin/env python3
"""Local HTTP API smoke tests. Never actually launch power commands."""
import importlib.util
import http.client
import json
import sys
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
spec=importlib.util.spec_from_file_location('bytecekserver',ROOT/'server.py')
server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)

class LauncherServerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd=ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        cls.port=cls.httpd.server_address[1]
        cls.thread=threading.Thread(target=cls.httpd.serve_forever,daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown();cls.httpd.server_close()

    def call(self, method, path, payload=None, token=True, origin=True):
        conn=http.client.HTTPConnection('127.0.0.1',self.port,timeout=2)
        headers={'Content-Type':'application/json'}
        if token: headers['X-Bytecek-Token']=server.TOKEN
        if origin: headers['Origin']='http://127.0.0.1:8765'
        conn.request(method,path, json.dumps(payload).encode() if payload is not None else None,headers)
        res=conn.getresponse();status=res.status;body=json.loads(res.read());conn.close();return status,body

    def test_config(self):
        status,data=self.call('GET','/api/config')
        self.assertEqual(status,200)
        self.assertEqual(data['token'],server.TOKEN)

    def test_reject_unauthorized_and_bad_origin(self):
        for token,origin in ((False,True),(True,False)):
            status,_=self.call('POST','/api/power',{'action':'poweroff'},token,origin)
            self.assertEqual(status,403)

    def test_reject_bad_url(self):
        for url in ('file:///etc/passwd','javascript:alert(1)','https://user:pass@example.com'):
            status,_=self.call('POST','/api/launch',{'url':url,'mode':'app'})
            self.assertEqual(status,400)

    def test_launch(self):
        with patch.object(server.window_state,'launch') as popen, patch.object(server,'BROWSER','/usr/bin/chromium'):
            status,data=self.call('POST','/api/launch',{'url':'https://spilled.kaooffline.top/','mode':'app'})
            self.assertEqual((status,data['ok']),(200,True))
            self.assertIn('--app=https://spilled.kaooffline.top/',popen.call_args[0][1])
            self.assertTrue(any('bytecek-sites' in arg for arg in popen.call_args[0][1]))

    def test_chrome_is_normal_window(self):
        with patch.object(server.window_state,'launch') as launch, patch.object(server,'BROWSER','/usr/bin/chromium'):
            status,_=self.call('POST','/api/launch',{'url':'https://www.google.com/','mode':'browser'})
            self.assertEqual(status,200)
            self.assertNotIn('--start-fullscreen',launch.call_args[0][1])
            self.assertIn('--start-maximized',launch.call_args[0][1])
            self.assertIn('chrome://newtab/',launch.call_args[0][1])
            self.assertTrue(launch.call_args.kwargs['normal'])

    def test_service_mode_requires_boolean(self):
        with patch.object(server.window_state,'set_service_mode') as toggle:
            status,_=self.call('POST','/api/service',{'enabled':'yes'})
            self.assertEqual(status,400)
            toggle.assert_not_called()
            status,data=self.call('POST','/api/service',{'enabled':True})
            self.assertEqual((status,data['service']),(200,True))
            toggle.assert_called_once_with(True)

    def test_brand_assets(self):
        for path, mime in (('/icons/spilled.png','image/png'),('/icons/ct24.svg','image/svg+xml'),('/icons/chrome.svg','image/svg+xml')):
            conn=http.client.HTTPConnection('127.0.0.1',self.port,timeout=2)
            conn.request('GET',path)
            res=conn.getresponse()
            self.assertEqual(res.status,200)
            self.assertEqual(res.getheader('Content-Type'),mime)
            self.assertTrue(res.read())
            conn.close()

    def test_reject_unknown_power(self):
        status,_=self.call('POST','/api/power',{'action':'sudo rm -rf /'})
        self.assertEqual(status,400)

    def ext_call(self, path, payload, origin='chrome-extension://abcdefghijklmnop'):
        conn=http.client.HTTPConnection('127.0.0.1',self.port,timeout=2)
        conn.request('POST',path,json.dumps(payload).encode(),{'Content-Type':'application/json','Origin':origin})
        res=conn.getresponse();status=res.status;body=json.loads(res.read());conn.close();return status,body

    def test_continue_watching_roundtrip(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp, patch.object(server,'STATE_DIR',Path(tmp)), patch.object(server,'CONTINUE_FILE',Path(tmp)/'c.json'):
            items=[{'id':'ep/1','show':'Show','label':'S1 E2','left':'12 min left','progress':140,'image':'javascript:alert(1)','url':'https://evil.example/'},{'show':'no id'}]
            status,data=self.ext_call('/api/spilled/continue',{'items':items})
            self.assertEqual((status,data['count']),(200,1))
            status,data=self.call('GET','/api/continue')
            item=data['items'][0]
            self.assertEqual(item['url'],'https://spilled.kaooffline.top/library/watch/ep%2F1')
            self.assertEqual((item['progress'],item['image']),(100,''))
            status,_=self.ext_call('/api/spilled/continue',{'items':[]},origin='https://evil.example')
            self.assertEqual(status,403)

    def test_episode_reuses_spilled_window_and_queues_jump(self):
        url='https://spilled.kaooffline.top/library/watch/abc'
        with patch.object(server.window_state,'launch',return_value=True) as launch, patch.object(server,'BROWSER','/usr/bin/chromium'):
            status,_=self.call('POST','/api/launch',{'url':url,'mode':'app'})
            self.assertEqual(status,200)
            self.assertEqual(launch.call_args[0][0],'app|https://spilled.kaooffline.top/')
        self.assertEqual(self.ext_call('/api/spilled/pending',{})[1],{'url':url})
        self.assertEqual(self.ext_call('/api/spilled/pending',{})[1],{})

    def test_font_served(self):
        conn=http.client.HTTPConnection('127.0.0.1',self.port,timeout=2)
        conn.request('GET','/fonts/BigShouldersDisplay.ttf');res=conn.getresponse();res.read();conn.close()
        self.assertEqual((res.status,res.getheader('Content-Type')),(200,'font/ttf'))

if __name__=='__main__':unittest.main()
