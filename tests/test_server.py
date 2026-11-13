#!/usr/bin/env python3
"""Local HTTP API smoke tests. Never actually launch power commands."""
import importlib.util
import http.client
import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
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
        with patch.object(server.subprocess,'Popen') as popen, patch.object(server,'BROWSER','/usr/bin/chromium'):
            status,data=self.call('POST','/api/launch',{'url':'https://spilled.kaooffline.top/','mode':'app'})
            self.assertEqual((status,data['ok']),(200,True))
            self.assertIn('--app=https://spilled.kaooffline.top/',popen.call_args[0][0])

    def test_reject_unknown_power(self):
        status,_=self.call('POST','/api/power',{'action':'sudo rm -rf /'})
        self.assertEqual(status,400)

if __name__=='__main__':unittest.main()
