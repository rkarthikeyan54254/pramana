#!/usr/bin/env python3
from pathlib import Path
import json,sys,threading,urllib.request
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from http.server import ThreadingHTTPServer
from product.http_server import Handler
srv=ThreadingHTTPServer(('127.0.0.1',0),Handler);port=srv.server_address[1];threading.Thread(target=srv.serve_forever,daemon=True).start()
try:
 with urllib.request.urlopen(f'http://127.0.0.1:{port}/mahaperiyava') as r:
  html=r.read().decode('utf-8');assert r.status==200 and 'Pramāṇa' in html and 'evidenceTemplate' in html
 for asset in ('app.js','styles.css','manifest.webmanifest'):
  with urllib.request.urlopen(f'http://127.0.0.1:{port}/mahaperiyava/{asset}') as r: assert r.status==200 and r.read()
 req=urllib.request.Request(f'http://127.0.0.1:{port}/v1/mahaperiyava/answer',data=json.dumps({'query':'Does Mahaperiyava teach the essential unity of Shiva and Vishnu?'}).encode(),headers={'Content-Type':'application/json'},method='POST')
 with urllib.request.urlopen(req) as r:
  out=json.load(r);assert out['answerable'] is True and out['status']=='grounded_answer_packet' and out['claims'] and out['evidence']
finally: srv.shutdown()
print('mahaperiyava-mobile-web-http: PASS')
