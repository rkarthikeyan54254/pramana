#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlparse
from product.service import dispatch

class Handler(BaseHTTPRequestHandler):
    def _send(self,status,obj):
        data=json.dumps(obj,ensure_ascii=False).encode('utf-8'); self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data)
    def do_GET(self):
        if urlparse(self.path).path=='/v1/health': self._send(200,dispatch('health',{}))
        else: self._send(404,{'status':'error','error':'not found'})
    def do_POST(self):
        path=urlparse(self.path).path; op={'/v1/verify':'verify','/v1/compare':'compare','/v1/trace':'trace'}.get(path)
        if not op: return self._send(404,{'status':'error','error':'not found'})
        try:
            n=int(self.headers.get('Content-Length','0')); payload=json.loads(self.rfile.read(n) or b'{}'); out=dispatch(op,payload); self._send(200,out)
        except Exception as e: self._send(400,{'status':'error','error':str(e)})
    def log_message(self,*_): pass

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--host',default='127.0.0.1'); ap.add_argument('--port',type=int,default=8765); a=ap.parse_args()
    print(f'Pramana local API http://{a.host}:{a.port}/v1/health',flush=True); ThreadingHTTPServer((a.host,a.port),Handler).serve_forever()
if __name__=='__main__': main()
