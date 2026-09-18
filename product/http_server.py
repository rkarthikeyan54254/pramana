#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,sys
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from product.service import dispatch
UI_ROOT=ROOT/'apps'/'mahaperiyava-mobile-web'
STATIC_ROUTES={
 '/mahaperiyava':('index.html','text/html; charset=utf-8'),
 '/mahaperiyava/':('index.html','text/html; charset=utf-8'),
 '/mahaperiyava/app.js':('app.js','application/javascript; charset=utf-8'),
 '/mahaperiyava/styles.css':('styles.css','text/css; charset=utf-8'),
 '/mahaperiyava/manifest.webmanifest':('manifest.webmanifest','application/manifest+json; charset=utf-8'),
}
class Handler(BaseHTTPRequestHandler):
 def _bytes(self,status,data,ctype):
  self.send_response(status);self.send_header('Content-Type',ctype);self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(data)
 def _json(self,status,obj): self._bytes(status,json.dumps(obj,ensure_ascii=False).encode('utf-8'),'application/json; charset=utf-8')
 def do_GET(self):
  path=urlparse(self.path).path
  if path=='/v1/health': return self._json(200,dispatch('health',{}))
  item=STATIC_ROUTES.get(path)
  if item:
   rel,ctype=item;target=UI_ROOT/rel
   if not target.exists(): return self._json(404,{'status':'error','error':'UI asset missing'})
   return self._bytes(200,target.read_bytes(),ctype)
  self._json(404,{'status':'error','error':'not found'})
 def do_POST(self):
  path=urlparse(self.path).path;op={'/v1/verify':'verify','/v1/compare':'compare','/v1/trace':'trace','/v1/mahaperiyava/answer':'mahaperiyava-answer'}.get(path)
  if not op: return self._json(404,{'status':'error','error':'not found'})
  try:
   n=int(self.headers.get('Content-Length','0'));payload=json.loads(self.rfile.read(n) or b'{}');self._json(200,dispatch(op,payload))
  except Exception as e: self._json(400,{'status':'error','error':str(e)})
 def log_message(self,*_): pass
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--host',default='127.0.0.1');ap.add_argument('--port',type=int,default=8765);a=ap.parse_args();print(f'Pramāṇa Mahaperiyava UI http://{a.host}:{a.port}/mahaperiyava',flush=True);ThreadingHTTPServer((a.host,a.port),Handler).serve_forever()
if __name__=='__main__': main()
