#!/usr/bin/env python3
from pathlib import Path
import sys,threading,json,urllib.request
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from http.server import ThreadingHTTPServer
from product.http_server import Handler
srv=ThreadingHTTPServer(('127.0.0.1',0),Handler); port=srv.server_address[1]; t=threading.Thread(target=srv.serve_forever,daemon=True); t.start()
with urllib.request.urlopen(f'http://127.0.0.1:{port}/v1/health') as r: h=json.load(r); assert h['status']=='ok'
req=urllib.request.Request(f'http://127.0.0.1:{port}/v1/verify',data=json.dumps({'claim':'Everything happens for a reason'}).encode(),headers={'Content-Type':'application/json'},method='POST')
with urllib.request.urlopen(req) as r: v=json.load(r); assert v['verified'] is False
srv.shutdown(); print('http-api-test: PASS')
